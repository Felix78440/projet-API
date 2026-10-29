# Noria — banque en ligne

L’application comprend une interface React/Vite et une API FastAPI avec une base
SQLite. Les opérations du site passent toutes par l’API ; la base de démonstration
est conservée dans `bank-api-develop/Back`.

## Démarrer l’application

Dans un premier terminal PowerShell, installer les dépendances Python et lancer l’API :

```powershell
cd .\bank-api-develop\Back
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Dans un second terminal, depuis la racine du dépôt, démarrer l’interface :

```powershell
npm install
npm run dev
```

Ouvrir l’adresse affichée par Vite (habituellement `http://localhost:5173`).
Le proxy Vite transmet automatiquement `/api` à l’API sur le port 8000.
La documentation interactive de l’API est disponible sur `http://localhost:8000/docs`.

## Comptes de démonstration

- Alice : `alice@banque.fr` / `alice1234`
- Bob : `bob@banque.fr` / `bob12345`

## Vérification

```powershell
npm test
npm run build
```

Pour exécuter les tests de l’API, dans `bank-api-develop/Back` :

```powershell
python -m pytest
```
