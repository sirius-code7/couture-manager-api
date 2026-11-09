# couture manager API

API REST de gestion d'un atelier de couture, développée avec **Python 3.12** et **FastAPI**.

## 1. Présentation du projet

Couture Manager API est une application destinée à faciliter la gestion quotidienne d'un atelier de couture.

Elle permet de centraliser les informations relatives aux clients, aux mesures, aux prestations, aux commandes, aux paiements et aux livraisons.

L'objectif est de simplifier le suivi des activités de l'atelier, d'améliorer l'organisation du travail et de faciliter le suivi financier.

## 2. Fonctionnalités principales

- **Authentification :** connexion sécurisée avec JWT.
- **Gestion des utilisateurs :** création, consultation, modification et gestion des comptes.
- **Gestion des clients :** enregistrement et suivi des clients.
- **Gestion des mesures :** enregistrement des mensurations des clients.
- **Gestion du catalogue :** gestion des types de vêtements et des prestations.
- **Gestion des commandes :** création et suivi des commandes selon leur état d'avancement.
- **Gestion des paiements :** enregistrement et suivi des règlements en FCFA.
- **Gestion des livraisons :** organisation et confirmation des livraisons.
- **Statistiques :** suivi du chiffre d'affaires, des paiements encaissés, des montants restants et des principaux clients.

## 3. Technologies utilisées

| Technologie | Utilisation |
|---|---|
| Python 3.12 | Langage de programmation |
| FastAPI | Développement de l'API REST |
| PostgreSQL | Base de données relationnelle |
| SQLAlchemy 2 | ORM et accès aux données |
| Pydantic | Validation des données |
| Alembic | Gestion des migrations |
| PyJWT | Authentification par jetons JWT |
| Argon2 | Hachage sécurisé des mots de passe |
| Pytest | Tests automatisés |
| Docker | Conteneurisation |

## 4. Organisation du projet

```text
couture-manager-api/
│
├── alembic/
│   └── versions/             # Historique des migrations
│
├── app/
│   ├── core/                 # Configuration et sécurité
│   ├── database/             # Connexion à PostgreSQL
│   ├── models/               # Modèles SQLAlchemy
│   ├── schemas/              # Schémas Pydantic
│   ├── routers/              # Routes de l'API
│   ├── services/             # Logique métier
│   ├── main.py               # Point d'entrée de l'API
│   └── seed.py               # Initialisation des données
│
├── tests/                    # Tests automatisés
│
├── .env.example              # Exemple de configuration
├── .gitignore
├── .dockerignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 5. Prérequis

Pour exécuter le projet localement, il faut disposer de :

- Python 3.12
- PostgreSQL
- Git
- pip

Docker et Docker Compose sont nécessaires uniquement pour le lancement conteneurisé.

## 6. Installation

### Cloner le dépôt

```bash
git clone <URL_DU_DEPOT>
cd couture-manager-api
```

### Créer un environnement virtuel

```bash
python -m venv .venv
```

Activer l'environnement virtuel sous Windows PowerShell :

```powershell
.venv\Scripts\Activate.ps1
```

Sous Linux ou macOS :

```bash
source .venv/bin/activate
```

### Installer les dépendances

```bash
pip install -r requirements.txt
```

## 7. Configuration de l'environnement

Créer un fichier `.env` à la racine du projet en prenant `.env.example` comme modèle.

Exemple de configuration :

```env
APP_NAME=Couture Manager API
APP_DESCRIPTION=API de gestion d'un atelier de couture.
APP_VERSION=1.0.0
ENVIRONMENT=development

DATABASE_URL=postgresql+psycopg://utilisateur:mot_de_passe@localhost:5432/couture_manager

JWT_SECRET_KEY=remplacer_par_une_cle_secrete
```

Adapter les paramètres de connexion à PostgreSQL selon l'environnement utilisé.

La clé JWT doit être remplacée par une valeur secrète suffisamment longue et aléatoire.

**Important :** le fichier `.env` contient des informations sensibles. Il ne doit jamais être publié ni exposé.

## 8. Base de données et migrations

Créer au préalable une base de données PostgreSQL nommée `couture_manager` et configurer les identifiants correspondants dans `.env`.

Appliquer les migrations :

```bash
python -m alembic upgrade head
```

Consulter la migration actuelle :

```bash
python -m alembic current
```

Consulter les migrations disponibles :

```bash
python -m alembic history
```

## 9. Initialisation des données

Pour initialiser le catalogue des prestations et créer un administrateur si aucun administrateur n'existe :

```bash
python -m app.seed
```

La création du premier administrateur nécessite les variables suivantes dans l'environnement :

```env
ADMIN_EMAIL=admin@example.com
ADMIN_NOM_COMPLET=Administrateur
ADMIN_PASSWORD=remplacer_par_un_mot_de_passe_securise
```

L'initialisation conserve les prestations et l'administrateur déjà présents.

## 10. Lancement de l'API

Démarrer le serveur de développement :

```bash
python -m uvicorn app.main:app --reload
```

L'API est accessible à l'adresse :

```text
http://127.0.0.1:8000
```

## 11. Documentation interactive

FastAPI génère automatiquement une documentation interactive.

- **Swagger UI :** http://127.0.0.1:8000/docs
- **ReDoc :** http://127.0.0.1:8000/redoc
- **Vérification de santé :** http://127.0.0.1:8000/health

Les routes métier sont regroupées sous le préfixe `/api/v1`.

## 12. Authentification et rôles

L'API utilise une authentification basée sur des jetons JWT.

Pour se connecter, utiliser la route :

```text
POST /api/v1/auth/login
```

Le champ `username` doit contenir l'adresse e-mail de l'utilisateur.

Les trois rôles disponibles sont :

| Rôle | Responsabilités |
|---|---|
| admin | Administration complète de l'application |
| accueil | Gestion des clients, commandes, paiements et livraisons |
| tailleur | Gestion des mesures et du suivi de production |

Les permissions sont contrôlées au niveau des routes.

## 13. Principales ressources de l'API

Les ressources sont accessibles sous `/api/v1`.

| Ressource | Préfixe |
|---|---|
| Authentification | `/auth` |
| Utilisateurs | `/utilisateurs` |
| Clients | `/clients` |
| Mesures | `/mesures` et `/clients/{client_id}/mesures` |
| Catalogue | `/catalogue` |
| Commandes | `/commandes` |
| Paiements | `/paiements` et `/commandes/{commande_id}/paiements` |
| Livraisons | `/livraisons` et `/commandes/{commande_id}/livraison` |
| Statistiques | `/statistiques` |

Pour consulter les méthodes HTTP, les paramètres, les schémas et les réponses, utiliser Swagger UI.

## 14. Tests automatisés

Les tests utilisent Pytest et FastAPI TestClient.

Une base de données de test distincte est nécessaire. Elle doit être configurée avec la variable `TEST_DATABASE_URL`.

Exemple de lancement sous PowerShell :

```powershell
$ligne = Get-Content .env | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
$url = ($ligne -replace '^DATABASE_URL=', '').Trim('"')
$env:TEST_DATABASE_URL = $url -replace '(/couture_manager)(\?.*)?$', '/couture_manager_test$2'
```

Exécuter l'ensemble des tests :

```bash
python -m pytest
```

Les tests couvrent notamment l'authentification, les utilisateurs, les clients, le catalogue, les mesures, les commandes, les paiements, les livraisons et les statistiques.

**Attention :** ne jamais utiliser la base de production comme base de test.

## 15. Lancement avec Docker

Le projet fournit un `Dockerfile` et un fichier `docker-compose.yml`.

Après installation et démarrage de Docker Desktop, configurer les variables nécessaires dans `.env`, notamment `JWT_SECRET_KEY`.

Démarrer les services :

```bash
docker compose up --build
```

L'API sera accessible à :

```text
http://localhost:8000
```

Consulter les journaux :

```bash
docker compose logs -f
```

Arrêter les services :

```bash
docker compose down
```

Les données PostgreSQL sont conservées dans un volume Docker nommé `postgres_data`.

## 16. Sécurité et bonnes pratiques

Le projet applique plusieurs principes de sécurité et de maintenabilité :

- Hachage des mots de passe avec Argon2.
- Authentification avec JWT.
- Contrôle des permissions selon les rôles.
- Validation des données avec Pydantic.
- Utilisation de variables d'environnement pour les paramètres sensibles.
- Utilisation de migrations Alembic pour faire évoluer la base de données.
- Séparation des routes, des schémas, des modèles et de la logique métier.
- Tests automatisés avec une base de données dédiée.

## 17. Devise et contexte métier

L'application est conçue pour un atelier de couture au Sénégal.

Les montants financiers sont exprimés en **francs CFA (FCFA)**.

Les moyens de paiement pris en charge sont :

- Espèces
- Wave
- Orange Money
- Virement
- Chèque

---

**Couture Manager API**  
API REST de gestion d'un atelier de couture ~ Python, FastAPI et PostgreSQL.