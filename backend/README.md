# Backend Flask

## Prerequis

- Python 3.10+

## Installation

```bash
python -m pip install -r requirements.txt
```

## Configuration

1. Copier `.env.example` vers `.env`.
2. Renseigner les identifiants OAuth Discord:
   - `DISCORD_CLIENT_ID`
   - `DISCORD_CLIENT_SECRET`
   - `DISCORD_REDIRECT_URI`

Le fichier `.env` est charge automatiquement au demarrage.

## Lancer le backend

```bash
python run.py
```

Le backend ecoute par defaut sur `http://127.0.0.1:5000`.

## Lancer les tests

```bash
python -m pytest -q
```
