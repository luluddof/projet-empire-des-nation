# Projet Empire des Nation

Architecture separee selon les bonnes pratiques:

- `backend/`: API Flask + login Discord OAuth2
- `frontend/`: application Vue (Vite)

## Demarrage rapide

### 1) Backend

```bash
cd backend
python -m pip install -r requirements.txt
python run.py
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3) Lancer les deux en meme temps (Windows)

Depuis la racine du projet:

```bat
start-dev.bat
```

## Login Discord

Le flux OAuth2 est gere par le backend:

- `GET /api/auth/discord/login`
- `GET /api/auth/discord/callback`
- `GET /api/auth/me`
- `POST /api/auth/logout`

### Configuration Discord pas a pas

1. Va sur [Discord Developer Portal](https://discord.com/developers/applications) puis cree une application.
2. Ouvre **OAuth2 > General** et copie:
   - `Client ID`
   - `Client Secret`
3. Dans **OAuth2 > Redirects**, ajoute exactement:
   - `http://127.0.0.1:5000/api/auth/discord/callback`
4. Copie `backend/.env.example` vers `backend/.env`, puis renseigne:
   - `DISCORD_CLIENT_ID`
   - `DISCORD_CLIENT_SECRET`
   - `DISCORD_REDIRECT_URI` (meme valeur que ci-dessus)
   - `FRONTEND_URL=http://localhost:5173`
5. Lance backend + frontend, ouvre `http://localhost:5173`, puis clique sur **Se connecter avec Discord**.
