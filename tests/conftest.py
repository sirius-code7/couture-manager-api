
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

test_database_url = os.getenv("TEST_DATABASE_URL")

if not test_database_url:
    raise RuntimeError(
        "DÃ©finissez TEST_DATABASE_URL avant de lancer les tests."
    )

database_name = make_url(test_database_url).database

if not database_name or not database_name.endswith("_test"):
    raise RuntimeError(
        "Les tests doivent utiliser une base dont le nom se termine par _test."
    )

os.environ["DATABASE_URL"] = test_database_url

from app.core.security import hash_password
from app.core.token import creer_access_token
from app.database.base import Base
from app.database.session import engine, get_db
from app.main import app
from app.models import (
    Client,
    Commande,
    HistoriqueStatut,
    Livraison,
    LigneCommande,
    Mesure,
    Paiement,
    TypeVetement,
    Utilisateur,
)


Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_connection():
    connection = engine.connect()
    transaction = connection.begin()

    yield connection

    transaction.rollback()
    connection.close()


@pytest.fixture
def db(db_connection):
    with Session(
        bind=db_connection,
        join_transaction_mode="create_savepoint",
    ) as session:
        yield session


@pytest.fixture
def client(db_connection):
    def override_get_db():
        with Session(
            bind=db_connection,
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def utilisateurs_test(db_connection):
    comptes = {
        "admin": ("admin@example.com", "admin"),
        "accueil": ("accueil@example.com", "accueil"),
        "tailleur": ("tailleur@example.com", "tailleur"),
        "inactif": ("inactif@example.com", "accueil"),
    }

    jetons = {}

    with Session(
        bind=db_connection,
        join_transaction_mode="create_savepoint",
    ) as session:
        for nom, (email, role) in comptes.items():
            utilisateur = Utilisateur(
                email=email,
                nom_complet=f"Compte {nom}",
                mot_de_passe_hash=hash_password("TestPassword123!"),
                role=role,
                actif=nom != "inactif",
            )

            session.add(utilisateur)
            session.flush()

            jetons[nom] = creer_access_token(
                utilisateur_id=utilisateur.id,
                role=utilisateur.role,
            )

        session.commit()

    return jetons

