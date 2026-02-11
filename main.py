"""
Système National des Retraites - Service CNR (Core Business)
Architecture SOA: Ce service orchestre les appels vers les services externes
"""
import os
import random
import httpx
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

# --- 1. CONFIGURATION SOA ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
ETAT_CIVIL_URL = os.getenv("ETAT_CIVIL_URL", "http://localhost:8001")
CNAS_URL = os.getenv("CNAS_URL", "http://localhost:8002")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- 2. MODÈLES DE BASE DE DONNÉES (DB Models) ---

class Beneficiary(Base):
    __tablename__ = "beneficiaires"

    id = Column(Integer, primary_key=True, index=True)
    nom_complet = Column(String, index=True)
    nss = Column(String, unique=True, index=True, nullable=False)

    # Indicateurs d'État
    en_vie = Column(Boolean, default=True)  # État Civil
    actif_travail = Column(Boolean, default=False)  # Affiliation CNAS
    eligible = Column(Boolean, default=True)  # Droit à la Pension

    # Motif Juridique (Loi 83-12)
    statut_juridique = Column(String, default="En attente d'audit")
    montant_pension = Column(Float, default=30000.0)  # Montant fictif en DA

    # Relation vers la réversion (One-to-One)
    reversion = relationship("Reversion", back_populates="beneficiaire_original", uselist=False)


class Reversion(Base):
    """
    Table pour les ayants-droit (Veuves/Orphelins)
    Créée automatiquement après le décès du bénéficiaire principal.
    """
    __tablename__ = "reversions"

    id = Column(Integer, primary_key=True, index=True)
    beneficiaire_id = Column(Integer, ForeignKey("beneficiaires.id"))
    nom_ayant_droit = Column(String)  # Ex: "Veuve de [Nom]"
    montant_reversion = Column(Float)  # % de la pension originale
    statut = Column(String, default="ACTIVE")

    beneficiaire_original = relationship("Beneficiary", back_populates="reversion")


# --- 3. SCHÉMAS PYDANTIC (Validation) ---

class BeneficiaryBase(BaseModel):
    nom_complet: str
    montant_pension: float = 30000.0


class BeneficiaryCreate(BeneficiaryBase):
    # Simulation: normal (vivant), worker (fraudeur), dead (décédé)
    type_simulation: str = "normal"


class ReversionResponse(BaseModel):
    id: int
    nom_ayant_droit: str
    montant_reversion: float
    statut: str
    model_config = ConfigDict(from_attributes=True)


class BeneficiaryResponse(BeneficiaryBase):
    id: int
    nss: str
    en_vie: bool
    actif_travail: bool
    eligible: bool
    statut_juridique: str
    reversion: Optional[ReversionResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- 4. UTILITAIRES: GÉNÉRATEUR NSS ---
def generer_nss(type_simulation: str = "normal") -> str:
    """
    Génère un NSS réaliste : AA-WW-SÉRIE-CLÉ
    - normal: Aléatoire (Vivant)
    - dead: Finit par '00' (Déclencheur Décès)
    - worker: Finit par '99' (Déclencheur Travailleur)
    """
    annee = datetime.now().year % 100
    wilaya = random.randint(1, 58)
    serie = random.randint(10000, 99999)

    if type_simulation == "dead":
        cle = "00"
    elif type_simulation == "worker":
        cle = "99"
    else:
        cle = str(random.choice([k for k in range(10, 89)]))

    return f"{annee:02d}-{wilaya:02d}-{serie}-{cle}"


# --- 5. DÉPENDANCES ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 6. CLIENT SOA: APPELS VERS SERVICES EXTERNES ---

async def appel_service_etat_civil(nss: str) -> dict:
    """
    VRAI APPEL SOA vers le Service État Civil (même si mocké)
    Endpoint: GET {ETAT_CIVIL_URL}/verify/{nss}
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ETAT_CIVIL_URL}/verify/{nss}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        print(f"[SOA ERROR] Service État Civil indisponible: {e}")
        # Mode dégradé: On suppose vivant par défaut
        return {"nss": nss, "en_vie": True, "date_deces": None, "error": "Service unavailable"}
    except httpx.HTTPStatusError as e:
        print(f"[SOA ERROR] État Civil HTTP {e.response.status_code}")
        return {"nss": nss, "en_vie": True, "date_deces": None, "error": f"HTTP {e.response.status_code}"}


async def appel_service_cnas(nss: str) -> dict:
    """
    VRAI APPEL SOA vers le Service CNAS
    Endpoint: GET {CNAS_URL}/employment/{nss}
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{CNAS_URL}/employment/{nss}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        print(f"[SOA ERROR] Service CNAS indisponible: {e}")
        # Mode dégradé: On suppose non-employé par défaut
        return {"nss": nss, "employe_actif": False, "employeur": None, "error": "Service unavailable"}
    except httpx.HTTPStatusError as e:
        print(f"[SOA ERROR] CNAS HTTP {e.response.status_code}")
        return {"nss": nss, "employe_actif": False, "employeur": None, "error": f"HTTP {e.response.status_code}"}


# --- 7. API CNR (SERVICE PRINCIPAL) ---
app = FastAPI(
    title="Service CNR - Caisse Nationale des Retraites",
    description="Service de gestion des retraites avec architecture SOA (Loi 83-12)",
    version="5.0-SOA"
)


@app.on_event("startup")
async def startup_event():
    """
    Événement de démarrage: Création des tables DB avec retry logic
    Attend que PostgreSQL soit prêt avant de créer les tables
    """
    import time
    max_retries = 10
    retry_interval = 2

    for attempt in range(max_retries):
        try:
            print(f"[STARTUP] Tentative {attempt + 1}/{max_retries} - Connexion à PostgreSQL...")
            Base.metadata.create_all(bind=engine)
            print("[STARTUP] ✓ Tables de base de données créées avec succès!")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[STARTUP] ⚠ Échec connexion DB: {e}")
                print(f"[STARTUP] Nouvelle tentative dans {retry_interval}s...")
                time.sleep(retry_interval)
            else:
                print(f"[STARTUP] ❌ ERREUR FATALE: Impossible de se connecter à la DB après {max_retries} tentatives")
                raise


@app.get("/health")
def health_check():
    """Point de santé pour le monitoring"""
    return {
        "service": "CNR",
        "status": "healthy",
        "version": "5.0-SOA",
        "external_services": {
            "etat_civil": ETAT_CIVIL_URL,
            "cnas": CNAS_URL
        }
    }


@app.post("/beneficiaires/", response_model=BeneficiaryResponse, status_code=status.HTTP_201_CREATED)
async def creer_dossier(dossier: BeneficiaryCreate, db: Session = Depends(get_db)):
    """
    [ENRÔLEMENT] Crée un nouveau dossier de retraite et attribue un NSS.
    """
    nss = generer_nss(dossier.type_simulation)

    if db.query(Beneficiary).filter(Beneficiary.nss == nss).first():
        raise HTTPException(status_code=409, detail="Erreur: Collision NSS détectée.")

    nouveau_benef = Beneficiary(
        nom_complet=dossier.nom_complet,
        nss=nss,
        montant_pension=dossier.montant_pension,
        statut_juridique="Dossier Créé (En attente de contrôle)"
    )

    db.add(nouveau_benef)
    db.commit()
    db.refresh(nouveau_benef)
    return nouveau_benef


@app.get("/beneficiaires/{id}/audit", response_model=BeneficiaryResponse)
async def auditer_dossier(id: int, db: Session = Depends(get_db)):
    """
    [CONTROLE SOA] Orchestre les appels vers État Civil et CNAS.
    Applique la Loi 83-12 et gère la Réversion automatique.

    Ce endpoint démontre:
    - Orchestration de services (ESB pattern)
    - Couplage faible (HTTP REST)
    - Résilience (mode dégradé si service down)
    """
    benef = db.query(Beneficiary).filter(Beneficiary.id == id).first()
    if not benef:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    print(f"\n=== [SOA ORCHESTRATION] Audit du dossier {benef.nss} ===")

    # 1. Appels SOA parallèles vers services externes
    print(f"→ Appel Service État Civil: {ETAT_CIVIL_URL}")
    print(f"→ Appel Service CNAS: {CNAS_URL}")

    import asyncio
    etat_civil_data, cnas_data = await asyncio.gather(
        appel_service_etat_civil(benef.nss),
        appel_service_cnas(benef.nss)
    )

    # 2. Extraction des réponses SOA
    est_vivant = etat_civil_data.get("en_vie", True)
    est_travailleur = cnas_data.get("employe_actif", False)

    print(f"← État Civil: en_vie={est_vivant}")
    print(f"← CNAS: employe_actif={est_travailleur}")

    # 3. Moteur de Décision (Business Logic)
    nouvelle_eligibilite = False
    nouveau_statut = "Indéterminé"

    # CAS A: DÉCÈS -> Bascule Réversion (Art. 30)
    if not est_vivant:
        nouvelle_eligibilite = False
        nouveau_statut = "CLOTURÉ: Décès confirmé par État Civil (Art. 6 - Transfert Art. 30)"

        # Création automatique de la Réversion
        reversion_existante = db.query(Reversion).filter(Reversion.beneficiaire_id == benef.id).first()
        if not reversion_existante:
            reversion = Reversion(
                beneficiaire_id=benef.id,
                nom_ayant_droit=f"Ayants-droit de {benef.nom_complet}",
                montant_reversion=benef.montant_pension * 0.75,
                statut="ACTIVE (Générée Automatiquement)"
            )
            db.add(reversion)
            print(f"✓ [AUTO] Pension de Réversion créée: {reversion.montant_reversion} DA")

    # CAS B: FRAUDE -> Suspension (Art. 8)
    elif est_travailleur:
        nouvelle_eligibilite = False
        nouveau_statut = "SUSPENDU: Activité Salariée détectée par CNAS (Infraction Art. 8)"
        print(f"⚠ [FRAUDE] Cumul pension + salaire détecté")

    # CAS C: CONFORME -> Validation
    else:
        nouvelle_eligibilite = True
        nouveau_statut = "VALIDE: Conforme aux articles 6 et 8 (Cessation d'activité vérifiée)"
        print(f"✓ [OK] Dossier conforme")

    # 4. Mise à jour Base de Données
    benef.en_vie = est_vivant
    benef.actif_travail = est_travailleur
    benef.eligible = nouvelle_eligibilite
    benef.statut_juridique = nouveau_statut

    db.commit()
    db.refresh(benef)

    print(f"=== [FIN ORCHESTRATION] ===\n")
    return benef


@app.get("/beneficiaires/", response_model=List[BeneficiaryResponse])
def lister_tous(db: Session = Depends(get_db)):
    """Liste tous les dossiers avec leur statut actuel."""
    return db.query(Beneficiary).all()