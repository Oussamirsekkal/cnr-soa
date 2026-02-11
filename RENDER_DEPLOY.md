# 🚀 Déploiement sur Render.com

Ce guide explique comment déployer les 3 microservices SOA sur Render.

## ⚠️ Erreur Courante: "could not translate host name 'db'"

Cette erreur signifie que votre app essaie de se connecter à `db:5432` (nom Docker Compose local) au lieu d'une vraie base de données Render.

**Solution:** Créer une base PostgreSQL sur Render et configurer `DATABASE_URL`.

---

## 📋 Méthode 1: Déploiement Automatique (Blueprint)

### Étape 1: Push vers GitHub
```bash
git add .
git commit -m "Add Render configuration"
git push origin main
```

### Étape 2: Créer les services sur Render
1. Allez sur [dashboard.render.com](https://dashboard.render.com)
2. Cliquez sur **New** → **Blueprint**
3. Connectez votre repo GitHub
4. Render détectera automatiquement `render.yaml` et créera:
   - 3 Web Services (CNR, État Civil, CNAS)
   - 1 PostgreSQL Database

---

## 📋 Méthode 2: Déploiement Manuel (Recommandé pour debug)

### Étape 1: Créer la Base PostgreSQL

1. Sur Render Dashboard → **New** → **PostgreSQL**
2. Configuration:
   - **Name:** `soa-postgres`
   - **Database:** `retraite_db`
   - **User:** `postgres`
   - **Region:** Frankfurt (EU) ou le plus proche
   - **Plan:** Free (pour tests) ou Starter ($7/mois)
3. Cliquez **Create Database**
4. **IMPORTANT:** Copiez l'**Internal Database URL** ou **External Database URL**

Exemple d'URL:
```
postgresql://postgres:XXXXX@dpg-xxxxx.frankfurt-postgres.render.com:5432/retraite_db
```

### Étape 2: Déployer Service État Civil

1. **New** → **Web Service**
2. Connectez votre repo GitHub
3. Configuration:
   - **Name:** `etat-civil-service`
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile`
   - **Docker Command:** `uvicorn service_etat_civil:app --host 0.0.0.0 --port 8000`
4. **Environment Variables:**
   ```
   PORT=8000
   ```
5. Cliquez **Create Web Service**
6. Attendez le déploiement, puis copiez l'URL (ex: `https://etat-civil-service.onrender.com`)

### Étape 3: Déployer Service CNAS

1. **New** → **Web Service**
2. Configuration:
   - **Name:** `cnas-service`
   - **Runtime:** Docker
   - **Docker Command:** `uvicorn service_cnas:app --host 0.0.0.0 --port 8000`
3. **Environment Variables:**
   ```
   PORT=8000
   ```
4. Copiez l'URL (ex: `https://cnas-service.onrender.com`)

### Étape 4: Déployer Service CNR (Principal)

1. **New** → **Web Service**
2. Configuration:
   - **Name:** `cnr-service`
   - **Runtime:** Docker
   - **Docker Command:** `uvicorn main:app --host 0.0.0.0 --port 8000`
3. **Environment Variables (TRÈS IMPORTANT):**
   ```
   PORT=8000
   DATABASE_URL=postgresql://postgres:XXXXX@dpg-xxxxx.frankfurt-postgres.render.com:5432/retraite_db
   ETAT_CIVIL_URL=https://etat-civil-service.onrender.com
   CNAS_URL=https://cnas-service.onrender.com
   ```
   
   > ⚠️ Remplacez les URLs par les vraies valeurs de vos services!

4. Cliquez **Create Web Service**

---

## ✅ Vérification du Déploiement

### Test du Health Check
```bash
# Service CNR
curl https://cnr-service.onrender.com/health

# Service État Civil
curl https://etat-civil-service.onrender.com/health

# Service CNAS
curl https://cnas-service.onrender.com/health
```

### Test Complet SOA
```bash
# 1. Créer un bénéficiaire
curl -X POST https://cnr-service.onrender.com/beneficiaires/ \
  -H "Content-Type: application/json" \
  -d '{"nom_complet": "Test Render", "type_simulation": "normal"}'

# 2. Audit SOA (appelle les 2 autres services)
curl https://cnr-service.onrender.com/beneficiaires/1/audit
```

### Swagger UI
- CNR: `https://cnr-service.onrender.com/docs`
- État Civil: `https://etat-civil-service.onrender.com/docs`
- CNAS: `https://cnas-service.onrender.com/docs`

---

## 🔧 Troubleshooting

### Erreur: "could not translate host name 'db'"
**Cause:** `DATABASE_URL` n'est pas configurée ou utilise encore `db` (Docker Compose).
**Solution:** Configurez `DATABASE_URL` avec l'URL PostgreSQL de Render.

### Erreur: "Connection refused" vers État Civil/CNAS
**Cause:** Les URLs des services sont incorrectes.
**Solution:** Vérifiez `ETAT_CIVIL_URL` et `CNAS_URL` dans les variables d'environnement.

### Service qui redémarre en boucle
**Cause:** Port incorrect.
**Solution:** Render utilise le port `10000` par défaut pour les services Docker. Vous avez 2 options:

**Option A (Recommandée):** Utiliser le port par défaut de Render
- Dans Environment Variables: `PORT=10000`
- Docker Command: `uvicorn main:app --host 0.0.0.0 --port 10000`

**Option B:** Configurer Render pour utiliser port 8000
- Allez dans Settings → Port → Changez à `8000`
- Dans Environment Variables: `PORT=8000`
- Docker Command: `uvicorn main:app --host 0.0.0.0 --port 8000`

> 💡 Le Dockerfile utilise `${PORT:-8000}` donc si vous ne spécifiez pas de Docker Command, il utilisera automatiquement la variable `PORT`.

### Base de données vide après redémarrage
**Cause:** Vous utilisez SQLite (fichier local non persistant).
**Solution:** Utilisez PostgreSQL de Render.

---

## 💰 Coûts Render

| Service | Plan | Coût |
|---------|------|------|
| PostgreSQL | Free | $0 (90 jours) |
| PostgreSQL | Starter | $7/mois |
| Web Service (x3) | Free | $0 (spin down après 15min) |
| Web Service (x3) | Starter | $7/mois chacun |

**Total minimum (avec free tier):** $0  
**Total production:** ~$28/mois (3 services + DB)

---

## 🔄 CI/CD Automatique

Render redéploie automatiquement à chaque push sur `main`. Pas besoin de GitHub Actions!

---

## 📁 Fichiers Modifiés

- `main.py`: Ajout du fix `postgres://` → `postgresql://`
- `Dockerfile`: Support de la variable `PORT`
- `render.yaml`: Configuration Blueprint (optionnel)

