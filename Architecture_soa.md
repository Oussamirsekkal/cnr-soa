# 🏗️ Architecture SOA - Implémentation Technique

## Vue d'Ensemble

Ce projet implémente une **vraie architecture SOA** avec **3 services indépendants** qui communiquent via HTTP REST:

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

## 📁 Structure des Fichiers SOA

```
/
├── main.py                    # Service CNR (Orchestrateur SOA)
├── service_etat_civil.py      # Service État Civil (Port 8001)
├── service_cnas.py            # Service CNAS (Port 8002)
├── docker-compose.yml         # Orchestration des 3 services
├── Dockerfile                 # Image commune aux services
├── requirements.txt           # Dépendances (avec httpx pour SOA)
└── README.md
```

## 🔄 Flux SOA Détaillé

### Scénario: Audit d'un Bénéficiaire

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

## 🌐 Contrats de Service (API Contracts)

### Service État Civil

**Endpoint:** `GET /verify/{nss}`

**Request:**
```http
GET http://localhost:8001/verify/25-16-12345-00
```

**Response:**
```json
{
  "nss": "25-16-12345-00",
  "en_vie": false,
  "date_deces": "2024-02-11T14:30:00",
  "lieu_naissance": "Alger (Mock)"
}
```

### Service CNAS

**Endpoint:** `GET /employment/{nss}`

**Request:**
```http
GET http://localhost:8002/employment/25-16-12345-99
```

**Response:**
```json
{
  "nss": "25-16-12345-99",
  "employe_actif": true,
  "employeur": "SONELGAZ (Mock)",
  "secteur_activite": "Énergie",
  "salaire_mensuel": 45000.0
}
```

## 🔧 Configuration SOA

### Variables d'Environnement (Service CNR)

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/retraite_db
ETAT_CIVIL_URL=http://etat-civil-api:8001
CNAS_URL=http://cnas-api:8002
```

### Network Docker (Isolation SOA)

Tous les services communiquent via le réseau `soa-network` défini dans docker-compose:

```yaml
networks:
  soa-network:
    driver: bridge
```

## 🧪 Tester l'Architecture SOA

### 1. Démarrer TOUS les services

```bash
docker-compose up --build
```

**Vérifier que les 4 conteneurs tournent:**
```bash
docker-compose ps

# Sortie attendue:
# cnr-service          uvicorn main:app ...           Up    0.0.0.0:8000->8000/tcp
# etat-civil-service   uvicorn service_etat_civil...  Up    0.0.0.0:8001->8001/tcp
# cnas-service         uvicorn service_cnas...        Up    0.0.0.0:8002->8002/tcp
# postgres-cnr         docker-entrypoint.sh...        Up    0.0.0.0:5432->5432/tcp
```

### 2. Tester chaque service INDIVIDUELLEMENT

**A. Service État Civil (isolé):**
```bash
curl http://localhost:8001/verify/25-16-12345-00

# Réponse: {"nss": "25-16-12345-00", "en_vie": false, ...}
```

**B. Service CNAS (isolé):**
```bash
curl http://localhost:8002/employment/25-16-12345-99

# Réponse: {"nss": "25-16-12345-99", "employe_actif": true, ...}
```

**C. Service CNR (orchestrateur):**
```bash
# 1. Créer un bénéficiaire "décédé"
curl -X POST http://localhost:8000/beneficiaires/ \
  -H "Content-Type: application/json" \
  -d '{"nom_complet": "Feu M. Brahim", "type_simulation": "dead"}'

# 2. Déclencher l'audit SOA
curl http://localhost:8000/beneficiaires/1/audit

# Dans les logs, vous verrez:
# [État Civil] Requête reçue pour NSS: 25-16-12345-00
# [CNAS] Requête reçue pour NSS: 25-16-12345-00
# ✓ [AUTO] Pension de Réversion créée: 22500.0 DA
```

### 3. Voir les Logs SOA en temps réel

```bash
# Tous les services
docker-compose logs -f

# Ou service par service
docker-compose logs -f cnr-api        # Orchestration
docker-compose logs -f etat-civil-api # Appels État Civil
docker-compose logs -f cnas-api       # Appels CNAS
```

## 🔐 Résilience SOA (Mode Dégradé)

Si un service externe tombe, le système CNR continue de fonctionner:

```python
# Dans main.py:
try:
    response = await client.get(f"{ETAT_CIVIL_URL}/verify/{nss}")
except httpx.RequestError:
    print("[SOA ERROR] Service État Civil indisponible")
    # Mode dégradé: on suppose vivant par défaut
    return {"en_vie": True, "error": "Service unavailable"}
```

**Test de résilience:**
```bash
# Arrêter le service État Civil
docker stop etat-civil-service

# Lancer un audit (il continuera de fonctionner)
curl http://localhost:8000/beneficiaires/1/audit
# Le service CNR suppose que le citoyen est vivant
```

## 📊 Avantages de cette Architecture

| Avantage | Implémentation |
|----------|----------------|
| **Indépendance** | Chaque service peut être redéployé sans toucher aux autres |
| **Scalabilité** | On peut lancer 10 instances du Service CNAS si besoin |
| **Testabilité** | Chaque service a son Swagger: /docs |
| **Interopérabilité** | N'importe quel langage peut appeler ces services (Python, Java, .NET) |
| **Gouvernance** | Le Ministère de l'Intérieur gère État Civil, le MTESS gère CNAS |

## 🚀 Passage en Production

### Option 1: Microservices sur Kubernetes

```yaml
# cnr-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cnr-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: cnr
        image: registry.gov.dz/cnr:latest
        env:
        - name: ETAT_CIVIL_URL
          value: "http://etat-civil-service:8001"
```

### Option 2: Service Mesh (Istio)

Pour gérer:
- Load balancing automatique
- Circuit breakers
- Retry policies
- Distributed tracing

## 📖 Références

- **Loi 83-12:** Base juridique
- **REST API Design:** Martin Fowler
- **Microservices Patterns:** Chris Richardson
- **SOA vs Microservices:** https://www.redhat.com/en/topics/microservices/soa-vs-microservices