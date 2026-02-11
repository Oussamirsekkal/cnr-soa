"""
Service CNAS - Caisse Nationale des Assurances Sociales (Mock)
Port: 8002
Rôle SOA: Vérification de l'activité salariée (détection du cumul pension + emploi)
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Service CNAS - Caisse Nationale des Assurances Sociales",
    description="API de vérification de l'affiliation salariale (Loi 83-12, Article 8)",
    version="1.0-Mock"
)


class EmploymentStatus(BaseModel):
    """Contrat de service (Service Contract)"""
    nss: str
    employe_actif: bool
    employeur: Optional[str] = None
    secteur_activite: Optional[str] = None
    salaire_mensuel: Optional[float] = None


@app.get("/health")
def health_check():
    return {
        "service": "CNAS",
        "status": "healthy",
        "ministere": "Travail, Emploi et Sécurité Sociale",
        "version": "1.0-Mock"
    }


@app.get("/employment/{nss}", response_model=EmploymentStatus)
def verifier_emploi(nss: str):
    """
    Endpoint SOA: Vérification de l'activité salariée

    Logique Mock:
    - NSS se terminant par "99" → Employé actif (FRAUDE - pour tests)
    - Autres NSS → Sans emploi (conforme)

    En production, cet endpoint interrogerait la vraie base CNAS
    avec les déclarations URSSAF/CASNOS.
    """
    print(f"[CNAS] Requête reçue pour NSS: {nss}")

    # Simulation: NSS finissant par "99" = Fraudeur (cumul)
    if nss.endswith("99"):
        return EmploymentStatus(
            nss=nss,
            employe_actif=True,
            employeur="SONELGAZ (Mock)",
            secteur_activite="Énergie",
            salaire_mensuel=45000.0
        )

    # Tous les autres cas: Sans emploi (conforme)
    return EmploymentStatus(
        nss=nss,
        employe_actif=False,
        employeur=None,
        secteur_activite=None,
        salaire_mensuel=None
    )


@app.get("/")
def root():
    return {
        "message": "Service CNAS - API Ready",
        "documentation": "/docs",
        "endpoint_principal": "/employment/{nss}"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)