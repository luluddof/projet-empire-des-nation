# Projet Empire des Nations

Architecture séparée selon les bonnes pratiques :

- `backend/` : API Flask + login Discord OAuth2 + gestion des ressources
- `frontend/` : application Vue 3 (Vite) + Vue Router

---

## Démarrage avec Docker (recommandé)

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé

### 1. Créer le fichier d'environnement backend

```bash
cp backend/.env.example backend/.env
```

Puis renseigner dans `backend/.env` :

```env
FLASK_SECRET_KEY=une-cle-secrete-aleatoire
DISCORD_CLIENT_ID=ton_client_id
DISCORD_CLIENT_SECRET=ton_client_secret
DISCORD_REDIRECT_URI=http://localhost:5173/api/auth/discord/callback
# IDs Discord des Maîtres du Jeu, séparés par des virgules
MJ_DISCORD_IDS=discord_id_mj1,discord_id_mj2
```

> **Note :** `FRONTEND_URL`, `FLASK_HOST` et `DISCORD_REDIRECT_URI` sont gérés par le `docker-compose.yml` (callback forcé sur `http://localhost:5173/api/auth/discord/callback`), inutile de les mettre dans `.env` pour Docker.

> **Session (connexion qui ne « tient » pas) :** le front parle au backend **via le proxy Vite** (`/api` sur le port **5173**). Le callback OAuth doit donc être **`http://localhost:5173/api/auth/discord/callback`** (à ajouter telle quelle dans Discord > OAuth2 > Redirects). Ne mélange pas **`localhost`** et **`127.0.0.1`** dans l’URL du navigateur : utilise **`http://localhost:5173`** pour ouvrir l’app.

### 2. Lancer tous les services

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Application (à utiliser dans le navigateur) | http://localhost:5173 |
| API Flask (direct, debug / health) | http://localhost:5000 |

Pour arrêter :

```bash
docker compose down
```

La base de données SQLite est persistée dans le volume Docker `empire_db` — elle survit aux redémarrages.

Pour tout réinitialiser (y compris la base) :

```bash
docker compose down -v
```

---

## Démarrage manuel (développement local)

### Prérequis

- Python 3.10+
- Node 18+

### 1. Backend

```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env   # puis renseigner les variables
python run.py
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # optionnel : VITE_API_BASE vide = proxy Vite vers le backend
npm run dev
```

### 3. Lancer les deux en même temps (Windows)

```bat
start-dev.bat
```

---

## Connexion Discord (OAuth2)

### Configuration Discord pas à pas

1. Va sur [Discord Developer Portal](https://discord.com/developers/applications) et crée une application.
2. Ouvre **OAuth2 > General** et copie :
   - `Client ID`
   - `Client Secret`
3. Dans **OAuth2 > Redirects**, ajoute exactement (une seule ligne, identique à `DISCORD_REDIRECT_URI` dans `backend/.env`) :
   - `http://localhost:5173/api/auth/discord/callback`
4. Renseigne ces valeurs dans `backend/.env`, puis **Save Changes** sur Discord.
5. Ouvre **`http://localhost:5173`** (pas `127.0.0.1`) et clique sur **Se connecter avec Discord**.

Tu peux vérifier l’URI vue par le serveur : `http://localhost:5173/api/auth/discord/redirect-uri` (JSON avec le champ `redirect_uri`).

### Flux d'authentification

| Endpoint | Description |
|---|---|
| `GET /api/auth/discord/login` | Redirige vers Discord |
| `GET /api/auth/discord/callback` | Callback OAuth2 |
| `GET /api/auth/me` | Retourne l'utilisateur connecté |
| `POST /api/auth/logout` | Déconnexion |

---

## Rôles

- **Joueur** : accès à ses propres stocks, gains passifs et historique.
- **MJ (Maître du Jeu)** : accès complet — gestion du catalogue de ressources, stocks de tous les joueurs.

Les IDs Discord des MJ sont définis via `MJ_DISCORD_IDS` dans `backend/.env`.

---

## Gains passifs

Chaque **mercredi et samedi à 00h00**, les ressources configurées en gain/perte passif sont automatiquement ajoutées ou retirées des stocks, et une transaction est enregistrée dans l'historique.
