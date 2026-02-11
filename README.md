# 🇩🇿 Système National des Retraites (Simulation SOA)

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> **Une démonstration d'architecture orientée services (SOA) appliquée à l'administration publique algérienne, automatisant la conformité à la Loi n° 83-12 relative à la retraite.**

---

## 📖 À Propos du Projet

Ce projet est une simulation technique d'un système de gestion des retraites "Cloud Native". Il remplace les tâches administratives manuelles par des **audits automatisés** via des micro-services interconnectés.

Le cœur du système est un moteur de règles juridiques qui applique strictement la loi algérienne en temps réel :

1. **Anti-Fraude (Art. 8) :** Détection automatique du cumul (Retraite + Salaire)
2. **Continuité des Droits (Art. 30) :** Bascule automatique vers une **Pension de Réversion** (Veuve/Orphelins) dès la confirmation du décès par l'État Civil

### 🎯 Objectifs

- ✅ Démontrer une architecture SOA moderne pour l'administration publique
- ✅ Automatiser la vérification de conformité légale (Loi 83-12)
- ✅ Simuler l'interopérabilité entre services gouvernementaux
- ✅ Fournir une API REST documentée et testable

---

## 🏗️ Architecture SOA - Implémentation Complète

Ce projet implémente une **vraie architecture SOA** avec **3 services indépendants** qui communiquent via HTTP REST.

### 📐 Vue d'Ensemble de l'Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE SOA                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                          │
│  │   Client     │  HTTP REST                               │
│  │  (Agent CNR) │────────────┐                             │
│  └──────────────┘            │                             │
│                              ▼                              │
│                    ┌──────────────────┐                     │
│                    │   CNR Service    │  Port 8000          │
│                    │  (Orchestrator)  │                     │
│                    └────────┬─────────┘                     │
│                             │                               │
│              ┌──────────────┼──────────────┐                │
│              │              │              │                │
│              ▼              ▼              ▼                │
│    ┌─────────────┐  ┌─────────────┐  ┌──────────┐          │
│    │ État Civil  │  │    CNAS     │  │PostgreSQL│          │
│    │  Service    │  │   Service   │  │    DB    │          │
│    │  Port 8001  │  │  Port 8002  │  │ Port 5432│          │
│    └─────────────┘  └─────────────┘  └──────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 Principes SOA Implémentés

Ce projet démontre les principes fondamentaux du SOA :

| Principe SOA | Implémentation | Bénéfice |
|--------------|----------------|----------|
| **Couplage Faible** | Les services communiquent via HTTP REST (pas de dépendances directes) | Chaque service peut être modifié/remplacé indépendamment |
| **Réutilisabilité** | Le Service État Civil peut être utilisé par d'autres ministères | Évite la duplication de code entre administrations |
| **Interopérabilité** | Protocoles standards (REST/JSON) | N'importe quel client peut consommer les services |
| **Autonomie** | Chaque service est déployé dans son propre conteneur | Aucun point de défaillance unique |
| **Découvrabilité** | API documentée via Swagger/OpenAPI | Les développeurs peuvent explorer les contrats de service |

### 🔄 Flux SOA Détaillé - Scénario Audit

**Exemple concret : Vérification d'un bénéficiaire**

```
1. Agent CNR → GET http://localhost:8000/beneficiaires/1/audit
   
2. Service CNR (main.py):
   ├─→ Récupère le bénéficiaire depuis PostgreSQL
   └─→ ORCHESTRATION SOA (appels parallèles):
       ├─→ GET http://etat-civil-api:8001/verify/25-16-12345-00
       └─→ GET http://cnas-api:8002/employment/25-16-12345-00

3. Service État Civil (service_etat_civil.py):
   └─→ Retourne: {"nss": "...", "en_vie": false, "date_deces": "2024-..."}

4. Service CNAS (service_cnas.py):
   └─→ Retourne: {"nss": "...", "employe_actif": false}

5. Service CNR:
   ├─→ MOTEUR DE RÈGLES applique Loi 83-12
   ├─→ Décision: DÉCÈS → Créer Pension de Réversion
   ├─→ Enregistre dans PostgreSQL
   └─→ Retourne le statut juridique à l'agent
```

### 🔧 Services Implémentés

#### 1️⃣ Service CNR (Core Business - Port 8000)
**Fichier:** `main.py`  
**Rôle :** Orchestrateur SOA et gestion des dossiers de retraite

**Endpoints :**
- `POST /beneficiaires/` - Création de dossier
- `GET /beneficiaires/{id}` - Consultation
- `GET /beneficiaires/{id}/audit` - Audit juridique (orchestre les appels SOA)
- `GET /health` - Health check

**Base de Données :** PostgreSQL (Tables: `beneficiaires`, `reversions`)

**Code d'orchestration SOA :**
```python
# Appels parallèles aux services externes
etat_civil_data, cnas_data = await asyncio.gather(
    appel_service_etat_civil(benef.nss),  # HTTP call
    appel_service_cnas(benef.nss)         # HTTP call
)
```

#### 2️⃣ Service État Civil (Port 8001)
**Fichier:** `service_etat_civil.py`  
**Rôle :** Vérification de l'existence physique (Loi 83-12, Article 6)

**Endpoint :** `GET /verify/{nss}`

**Contrat de Service (Response) :**
```json
{
  "nss": "25-16-12345-00",
  "en_vie": false,
  "date_deces": "2024-02-11T14:30:00",
  "lieu_naissance": "Alger (Mock)"
}
```

**Logique Mock :** NSS se terminant par "00" → Décédé (pour tests)

#### 3️⃣ Service CNAS (Port 8002)
**Fichier:** `service_cnas.py`  
**Rôle :** Vérification d'activité salariée (Loi 83-12, Article 8)

**Endpoint :** `GET /employment/{nss}`

**Contrat de Service (Response) :**
```json
{
  "nss": "25-16-12345-99",
  "employe_actif": true,
  "employeur": "SONELGAZ (Mock)",
  "secteur_activite": "Énergie",
  "salaire_mensuel": 45000.0
}
```

**Logique Mock :** NSS se terminant par "99" → Employé actif (FRAUDE)

### 🌐 Communication Inter-Services (SOA)

**Protocole :** HTTP REST (Synchrone)  
**Format :** JSON  
**Client HTTP :** `httpx` (asynchrone)  
**Authentification :** Non implémentée (Token Bearer en production)

**Configuration SOA (Variables d'environnement) :**
```env
# Service CNR
DATABASE_URL=postgresql://postgres:postgres@db:5432/retraite_db
ETAT_CIVIL_URL=http://etat-civil-api:8001
CNAS_URL=http://cnas-api:8002
```

**Network Docker (Isolation) :**
```yaml
networks:
  soa-network:
    driver: bridge
```

### 🔐 Résilience SOA (Mode Dégradé)

Si un service externe tombe, le système CNR continue de fonctionner:

```python
try:
    response = await client.get(f"{ETAT_CIVIL_URL}/verify/{nss}")
    return response.json()
except httpx.RequestError:
    print("[SOA ERROR] Service État Civil indisponible")
    # Mode dégradé: on suppose vivant par défaut
    return {"en_vie": True, "error": "Service unavailable"}
```

**Test de résilience :**
```bash
# Arrêter le service État Civil
docker stop etat-civil-service

# Lancer un audit (il continuera de fonctionner)
curl http://localhost:8000/beneficiaires/1/audit
# Le service CNR suppose que le citoyen est vivant
```

### 🎭 Avantages de cette Architecture SOA

| Avantage | Implémentation Concrète |
|----------|-------------------------|
| **Indépendance** | Chaque service peut être redéployé sans toucher aux autres |
| **Scalabilité Horizontale** | On peut lancer 10 instances du Service CNAS si le trafic augmente |
| **Testabilité** | Chaque service a son Swagger : `/docs` (8000, 8001, 8002) |
| **Interopérabilité** | N'importe quel langage peut appeler ces services (Python, Java, .NET) |
| **Gouvernance Distribuée** | Le Ministère de l'Intérieur gère État Civil, le MTESS gère CNAS |
| **Résilience** | Si État Civil tombe, le système continue (mode dégradé) |

### 📦 Structure des Fichiers SOA

```
/
├── main.py                    # Service CNR (Orchestrateur SOA - Port 8000)
├── service_etat_civil.py      # Service État Civil (Port 8001)
├── service_cnas.py            # Service CNAS (Port 8002)
├── docker-compose.yml         # Orchestration des 4 conteneurs
├── Dockerfile                 # Image commune aux services
├── requirements.txt           # Dépendances (httpx pour SOA)
└── README.md                  # Ce fichier
```

### 🔧 Stack Technologique

| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| **Backend** | Python | 3.12 | Langage principal |
| **Framework API** | FastAPI | 0.109+ | REST API haute performance |
| **Communication SOA** | httpx | 0.26+ | Client HTTP asynchrone pour appels inter-services |
| **Base de Données** | PostgreSQL | 16 | Persistance relationnelle |
| **ORM** | SQLAlchemy | 2.0+ | Mapping objet-relationnel |
| **Conteneurisation** | Docker | Latest | Isolation des services |
| **Orchestration** | Docker Compose | v2+ | Gestion multi-conteneurs |
| **Serveur ASGI** | Uvicorn | Latest | Serveur web asynchrone |
| **Validation** | Pydantic | 2.0+ | Validation des données |

### 🚀 Évolution vers Microservices

Ce projet démontre une **architecture SOA** avec services séparés. Pour évoluer vers une vraie architecture microservices en production :

```bash
# Architecture cible (production)
Kubernetes Cluster
├── cnr-service (3 replicas)          # Load balanced
├── etat-civil-service (2 replicas)   # Owned by Ministère Intérieur
├── cnas-service (2 replicas)         # Owned by MTESS
├── casnos-service (NEW)              # Travailleurs non-salariés
├── api-gateway (Nginx/Kong)          # Entry point
└── PostgreSQL (Managed DB)           # render cloud
```

**Chaque service aurait :**
- Son propre repository Git
- Son pipeline CI/CD (GitHub Actions / GitLab CI)
- Son équipe de développement
- Sa propre base de données (Database per Service pattern)
- Son SLA et monitoring

---

## ⚖️ Logique Juridique (Implémentée)

Le code ne se contente pas de stocker des données, il **décide du sort des dossiers** en fonction des articles de loi :

| Article de Loi (83-12) | Règle Métier Implémentée | Action Système |
|------------------------|--------------------------|----------------|
| **Article 6** | Vérification de l'existence physique | Appel API État Civil. Si décès : Clôture |
| **Article 8** | Interdiction de cumul avec un emploi | Appel API CNAS. Si actif : Suspension |
| **Article 30** | Droit de réversion aux ayants-droit | Création automatique d'une entrée Reversion (75% du montant) |

### 🔐 Moteur de Règles

```python
# Pseudo-code du moteur de décision
def audit_conformite(beneficiaire):
    # Règle 1: Existence physique (Art. 6)
    if not etat_civil.is_alive(beneficiaire.nss):
        return CLOTURE + create_reversion()
    
    # Règle 2: Anti-cumul (Art. 8)
    if cnas.is_employed(beneficiaire.nss):
        return SUSPENSION
    
    # Règle 3: Montant conforme
    if beneficiaire.montant < SMIG_RETRAITE:
        return AJUSTEMENT_REQUIS
    
    return VALIDE
```

---

## 🚀 Installation & Démarrage

### Prérequis

- ✅ **Docker Desktop** installé et lancé ([Télécharger](https://www.docker.com/products/docker-desktop))
- ✅ **Git** pour cloner le projet
- ✅ **Port 8000** disponible sur votre machine

### 1️⃣ Clonage du Projet

```bash
# Cloner le dépôt
git clone https://github.com/Oussamirsekkal/cnr-soa.git
cd SOA-test
```

### 2️⃣ Lancement de l'Application

```bash
# Construire et démarrer tous les services
docker-compose up --build

# OU en mode détaché (arrière-plan)
docker-compose up -d --build
```

**Temps de démarrage :** ~30-60 secondes (téléchargement des images + build)

### 3️⃣ Vérification du Démarrage

```bash
# Vérifier que les conteneurs tournent
docker-compose ps

# Voir les logs en temps réel
docker-compose logs -f
```

**Sortie attendue :**
```
NAME                COMMAND                  SERVICE             STATUS
retraite-api-1      "uvicorn main:app ..."   api                 running
retraite-db-1       "docker-entrypoint..."   db                  running
```

### 4️⃣ Accès à l'Application

| Service | URL | Description |
|---------|-----|-------------|
| **API Documentation (Swagger)** | http://localhost:8000/docs | Interface interactive pour tester l'API |
| **API Alternative (ReDoc)** | http://localhost:8000/redoc | Documentation alternative |
| **API Root** | http://localhost:8000 | Point d'entrée de l'API |
| **Health Check** | http://localhost:8000/health | Vérification du statut |

---

## 🧪 Guide de Test (Scénarios SOA)

Le système utilise un générateur de NSS intelligent pour simuler des cas réels et démontrer l'orchestration SOA.

### 🔍 Vérification de l'Architecture SOA

**Avant de tester les scénarios, vérifiez que les 4 conteneurs sont actifs :**

```bash
docker-compose ps

# Sortie attendue:
# NAME                  STATUS              PORTS
# cnr-service          Up                  0.0.0.0:8000->8000/tcp
# etat-civil-service   Up                  0.0.0.0:8001->8001/tcp
# cnas-service         Up                  0.0.0.0:8002->8002/tcp
# postgres-cnr         Up                  0.0.0.0:5432->5432/tcp
```

**Tester chaque service individuellement :**

```bash
# Service CNR
curl http://localhost:8000/health

# Service État Civil (isolé)
curl http://localhost:8001/verify/25-16-12345-00
# Réponse: {"nss":"25-16-12345-00","en_vie":false,...}

# Service CNAS (isolé)
curl http://localhost:8002/employment/25-16-12345-99
# Réponse: {"nss":"25-16-12345-99","employe_actif":true,...}
```

### 🟢 Scénario A : Le Retraité Modèle

**Cas :** Citoyen vivant, ne travaille pas → Dossier VALIDE

```bash
# 1. Création du dossier (Simulation Type: "normal")
curl -X POST "http://localhost:8000/beneficiaires/" \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "M. Ahmed Benmouhoub",
    "type_simulation": "normal"
  }'

# Réponse attendue (ID = 1)
{
  "id": 1,
  "nss": "25-16-12345-67",
  "nom_complet": "M. Ahmed Benmouhoub",
  "montant_pension": 30000.0,
  "eligible": true,
  "statut_juridique": "Dossier Créé (En attente de contrôle)"
}

# 2. Audit du dossier (DÉCLENCHE L'ORCHESTRATION SOA)
curl -X GET "http://localhost:8000/beneficiaires/1/audit"

# Dans les logs (docker-compose logs -f), vous verrez:
# [SOA ORCHESTRATION] Audit du dossier 25-16-12345-67
# → Appel Service État Civil: http://etat-civil-api:8001
# → Appel Service CNAS: http://cnas-api:8002
# ← État Civil: en_vie=true
# ← CNAS: employe_actif=false
# ✓ [OK] Dossier conforme
```

**✅ Résultat attendu :**
```json
{
  "id": 1,
  "nss": "25-16-12345-67",
  "nom_complet": "M. Ahmed Benmouhoub",
  "montant_pension": 30000.0,
  "en_vie": true,
  "actif_travail": false,
  "eligible": true,
  "statut_juridique": "VALIDE: Conforme aux articles 6 et 8 (Cessation d'activité vérifiée)",
  "reversion": null
}
```

---

### 🔴 Scénario B : La Fraude au Cumul (SOA Anti-Fraude)

**Cas :** Citoyen qui perçoit une retraite ET un salaire déclaré à la CNAS

```bash
# 1. Création (Simulation Type: "worker")
curl -X POST "http://localhost:8000/beneficiaires/" \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "M. Karim Le Malin",
    "type_simulation": "worker"
  }'

# Réponse: {"id": 2, "nss": "25-16-12345-99", ...}

# 2. Audit SOA (détection automatique du cumul)
curl -X GET "http://localhost:8000/beneficiaires/2/audit"

# Logs SOA:
# [SOA ORCHESTRATION] Audit du dossier 25-16-12345-99
# ← État Civil: en_vie=true
# ← CNAS: employe_actif=true  ⚠️ ALERTE FRAUDE
# ⚠ [FRAUDE] Cumul pension + salaire détecté
```

**❌ Résultat attendu :**
```json
{
  "id": 2,
  "nss": "25-16-12345-99",
  "nom_complet": "M. Karim Le Malin",
  "montant_pension": 30000.0,
  "en_vie": true,
  "actif_travail": true,
  "eligible": false,
  "statut_juridique": "SUSPENDU: Activité Salariée détectée par CNAS (Infraction Art. 8)",
  "reversion": null
}
```

---

### ⚫ Scénario C : Décès & Réversion Automatique (SOA Art. 30)

**Cas :** Décès du bénéficiaire → Orchestration SOA → Transfert automatique à la veuve

```bash
# 1. Création (Simulation Type: "dead")
curl -X POST "http://localhost:8000/beneficiaires/" \
  -H "Content-Type: application/json" \
  -d '{
    "nom_complet": "Feu M. Brahim",
    "type_simulation": "dead"
  }'

# Réponse: {"id": 3, "nss": "25-16-12345-00", ...}

# 2. Audit (Déclencheur de la loi Art. 30)
curl -X GET "http://localhost:8000/beneficiaires/3/audit"

# Logs SOA:
# [SOA ORCHESTRATION] Audit du dossier 25-16-12345-00
# ← État Civil: en_vie=false ☠️ DÉCÈS CONFIRMÉ
# ← CNAS: employe_actif=false
# ✓ [AUTO] Pension de Réversion créée: 22500.0 DA (75% de 30000)
```

**☠️ Résultat attendu :**
```json
{
  "id": 3,
  "nss": "25-16-12345-00",
  "nom_complet": "Feu M. Brahim",
  "montant_pension": 30000.0,
  "en_vie": false,
  "actif_travail": false,
  "eligible": false,
  "statut_juridique": "CLOTURÉ: Décès confirmé par État Civil (Art. 6 - Transfert Art. 30)",
  "reversion": {
    "id": 1,
    "beneficiaire_id": 3,
    "nom_ayant_droit": "Ayants-droit de Feu M. Brahim",
    "montant_reversion": 22500.0,
    "statut": "ACTIVE (Générée Automatiquement)"
  }
}
```

---

### 🔬 Scénario D : Test de Résilience SOA (Mode Dégradé)

**Cas :** Service État Civil hors ligne → Le système continue de fonctionner

```bash
# 1. Arrêter le service État Civil
docker stop etat-civil-service

# 2. Créer un bénéficiaire
curl -X POST "http://localhost:8000/beneficiaires/" \
  -H "Content-Type: application/json" \
  -d '{"nom_complet": "M. Test Resilience", "type_simulation": "normal"}'

# 3. Lancer l'audit (le service CNR continue malgré l'erreur)
curl http://localhost:8000/beneficiaires/4/audit

# Logs:
# [SOA ERROR] Service État Civil indisponible: ...
# Mode dégradé: On suppose vivant par défaut
# ← CNAS: employe_actif=false
# ✓ [OK] Dossier conforme (mode dégradé)

# 4. Redémarrer le service
docker start etat-civil-service
```

**Résultat :** Le système fonctionne en mode dégradé et suppose que le citoyen est vivant.

---

### 📊 Voir les Logs SOA en Temps Réel

```bash
# Tous les services
docker-compose logs -f

# Ou service par service
docker-compose logs -f cnr-api        # Orchestration
docker-compose logs -f etat-civil-api # Appels État Civil
docker-compose logs -f cnas-api       # Appels CNAS
```

---

## 🛠️ Maintenance & Commandes Utiles

### Commandes Essentielles Docker

| Goal | Command | Why/When to use? |
|------|---------|------------------|
| **Start & Build** | `docker-compose up --build` | Use this 90% of the time. It builds the code changes and starts the app. |
| **Start (Fast)** | `docker-compose up` | Starts existing containers without rebuilding. Good if you didn't change code. |
| **Stop** | `docker-compose down` | Stops the app and removes the containers. |
| **The "Hard Reset"** | `docker-compose down -v` | ⚠️ CRITICAL FIX. Stops app AND deletes the Database Volume. Use this if you changed `models.py` or DB columns. |
| **View Logs** | `docker-compose logs -f` | Watch the console output in real-time (to see errors). |
| **Clean Docker** | `docker system prune -a` | Deletes all unused images and cache to free up space (Nuclear option). |

### Commandes de Debug Avancées

```bash
# Entrer dans le conteneur API
docker-compose exec api /bin/bash

# Entrer dans PostgreSQL
docker-compose exec db psql -U postgres -d retraite_db

# Voir l'utilisation des ressources
docker stats

# Logs d'un service spécifique
docker-compose logs -f api
```

### Scripts SQL Utiles

```sql
-- Lister tous les bénéficiaires
SELECT * FROM beneficiaires;

-- Compter les réversions actives
SELECT COUNT(*) FROM reversions;

-- Trouver les dossiers suspects (cumul)
SELECT * FROM beneficiaires WHERE nss LIKE '%999%';
```

---

## 🔄 Workflow de Développement

### Modifier le Code

1. Éditez `main.py` ou d'autres fichiers
2. Arrêtez les conteneurs : `docker-compose down`
3. Relancez avec rebuild : `docker-compose up --build`

### Ajouter une Dépendance

1. Ajoutez la lib dans `requirements.txt`
2. Rebuild l'image : `docker-compose build api`
3. Relancez : `docker-compose up`

### Migration de Base de Données (Alembic)

```bash
# Installer Alembic
pip install alembic

# Initialiser
alembic init alembic

# Créer une migration
alembic revision --autogenerate -m "Description"

# Appliquer les migrations
alembic upgrade head
```


---

## 📂 Structure des Fichiers

```
/
├── main.py              # Le cerveau (API, Logique, Modèles)
├── Dockerfile           # La recette pour construire l'image Linux
├── docker-compose.yml   # Le chef d'orchestre (Lie l'App et la DB)
├── requirements.txt     # La liste des ingrédients (Libs Python)
└── README.md            # Ce fichier
```

---

## 🧪 Tests Automatisés (Optionnel)

### Installation de Pytest

```bash
pip install pytest pytest-asyncio httpx
```

### Exemple de Test

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_beneficiaire():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/beneficiaires/",
            json={"nom_complet": "Test User", "type_simulation": "normal"}
        )
    assert response.status_code == 200
    assert "nss" in response.json()
```

### Lancer les Tests

```bash
pytest tests/ -v
```

---

## 📊 Monitoring & Observabilité

### Logs Structurés

```python
# Ajouter dans main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Health Check Endpoint

```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }
```

---

## 🔒 Sécurité

### Recommandations de Production

- ✅ Utiliser des secrets pour les mots de passe DB
- ✅ Activer HTTPS (TLS/SSL)
- ✅ Implémenter l'authentification JWT
- ✅ Limiter les requêtes (Rate Limiting)
- ✅ Valider toutes les entrées utilisateur

### Exemple d'Authentification JWT

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected")
def protected_route(credentials = Depends(security)):
    # Valider le token
    return {"message": "Accès autorisé"}
```

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

1. **Fork** le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Commitez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une **Pull Request**

---

## 📄 Licence

Ce projet est sous licence **MIT** - voir le fichier [LICENSE](LICENSE) pour plus de détails.






## 🔗 Liens Utiles

- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Guide](https://www.postgresql.org/docs/)
- [Loi 83-12 (Texte Intégral)](https://www.joradp.dz/)

---

