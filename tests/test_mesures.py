from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models.commande import Commande
from app.models.utilisateur import Utilisateur


def entetes(token):
    return {"Authorization": f"Bearer {token}"}


def donnees_client(telephone="771234567"):
    return {
        "nom": "Diop",
        "prenom": "Mamadou",
        "telephone": telephone,
        "email": "mamadou@example.com",
        "adresse": "Dakar, Senegal",
        "genre": "homme",
        "notes": "Client de test",
    }


def donnees_mesure(**modifications):
    donnees = {"taille_cm": 175}
    donnees.update(modifications)
    return donnees


def creer_client(client, token):
    response = client.post(
        "/api/v1/clients",
        json=donnees_client(),
        headers=entetes(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


def creer_mesure(client, client_id, token, donnees=None):
    if donnees is None:
        donnees = donnees_mesure()

    response = client.post(
        f"/api/v1/clients/{client_id}/mesures",
        json=donnees,
        headers=entetes(token),
    )
    return response


def test_creation_mesure_tailleur(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)

    response = creer_mesure(client, client_id, token)

    assert response.status_code == 201
    assert response.json()["client_id"] == client_id
    assert response.json()["taille_cm"] == "175.00"


@pytest.mark.parametrize("role", ["admin", "accueil"])
def test_creation_mesure_interdite_aux_autres_roles(
    client,
    utilisateurs_test,
    role,
):
    token = utilisateurs_test[role]
    client_id = creer_client(client, token)

    response = creer_mesure(client, client_id, token)

    assert response.status_code == 403


def test_creation_mesure_sans_authentification(client):
    response = client.post(
        "/api/v1/clients/1/mesures",
        json=donnees_mesure(),
    )

    assert response.status_code == 401


def test_creation_mesure_client_inexistant(client, utilisateurs_test):
    response = creer_mesure(
        client,
        999999,
        utilisateurs_test["tailleur"],
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "donnees",
    [
        {},
        {"taille_cm": 0},
        {"taille_cm": -10},
        {"taille_cm": 301},
    ],
)
def test_creation_mesure_donnees_invalides(
    client,
    utilisateurs_test,
    donnees,
):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)

    response = creer_mesure(client, client_id, token, donnees)

    assert response.status_code == 422


def test_creation_mesure_date_future(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)

    response = creer_mesure(
        client,
        client_id,
        token,
        donnees_mesure(
            date_prise=(date.today() + timedelta(days=1)).isoformat()
        ),
    )

    assert response.status_code == 422


def test_lister_mesures_client(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)

    creation = creer_mesure(client, client_id, token)
    response = client.get(
        f"/api/v1/clients/{client_id}/mesures",
        headers=entetes(token),
    )

    assert creation.status_code == 201
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_lister_mesures_client_inexistant(client, utilisateurs_test):
    response = client.get(
        "/api/v1/clients/999999/mesures",
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 404


def test_lister_mesures_sans_authentification(client):
    response = client.get("/api/v1/clients/1/mesures")

    assert response.status_code == 401


def test_consulter_derniere_mesure(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)

    premiere = creer_mesure(
        client,
        client_id,
        token,
        donnees_mesure(
            date_prise=(date.today() - timedelta(days=2)).isoformat()
        ),
    )
    derniere = creer_mesure(
        client,
        client_id,
        token,
        donnees_mesure(
            date_prise=date.today().isoformat(),
            taille_cm=180,
        ),
    )

    response = client.get(
        f"/api/v1/clients/{client_id}/mesures/derniere",
        headers=entetes(token),
    )

    assert premiere.status_code == 201
    assert derniere.status_code == 201
    assert response.status_code == 200
    assert response.json()["taille_cm"] == "180.00"


def test_derniere_mesure_client_inexistant(client, utilisateurs_test):
    response = client.get(
        "/api/v1/clients/999999/mesures/derniere",
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 404


def test_derniere_mesure_sans_mesure(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)

    response = client.get(
        f"/api/v1/clients/{client_id}/mesures/derniere",
        headers=entetes(token),
    )

    assert response.status_code == 404


def test_consulter_mesure(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)
    creation = creer_mesure(client, client_id, token)

    mesure_id = creation.json()["id"]
    response = client.get(
        f"/api/v1/mesures/{mesure_id}",
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == mesure_id


def test_consulter_mesure_inexistante(client, utilisateurs_test):
    response = client.get(
        "/api/v1/mesures/999999",
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 404


def test_modifier_mesure_tailleur(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)
    creation = creer_mesure(client, client_id, token)

    mesure_id = creation.json()["id"]
    response = client.patch(
        f"/api/v1/mesures/{mesure_id}",
        json={"taille_cm": 180, "notes": "Mesure actualisee"},
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["taille_cm"] == "180.00"
    assert response.json()["notes"] == "Mesure actualisee"


def test_modifier_mesure_interdit_accueil(client, utilisateurs_test):
    token_tailleur = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token_tailleur)
    creation = creer_mesure(client, client_id, token_tailleur)

    response = client.patch(
        f"/api/v1/mesures/{creation.json()['id']}",
        json={"taille_cm": 180},
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 403


def test_modifier_mesure_valeur_invalide(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)
    creation = creer_mesure(client, client_id, token)

    response = client.patch(
        f"/api/v1/mesures/{creation.json()['id']}",
        json={"taille_cm": 0},
        headers=entetes(token),
    )

    assert response.status_code == 422


def test_modifier_mesure_sans_mesure_restante(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)
    creation = creer_mesure(client, client_id, token)

    response = client.patch(
        f"/api/v1/mesures/{creation.json()['id']}",
        json={"taille_cm": None},
        headers=entetes(token),
    )

    assert response.status_code == 422


def test_modifier_mesure_date_vide(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)
    creation = creer_mesure(client, client_id, token)

    response = client.patch(
        f"/api/v1/mesures/{creation.json()['id']}",
        json={"date_prise": None},
        headers=entetes(token),
    )

    assert response.status_code == 422


def test_modifier_mesure_inexistante(client, utilisateurs_test):
    response = client.patch(
        "/api/v1/mesures/999999",
        json={"taille_cm": 180},
        headers=entetes(utilisateurs_test["tailleur"]),
    )

    assert response.status_code == 404


def test_supprimer_mesure_tailleur(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)
    creation = creer_mesure(client, client_id, token)

    mesure_id = creation.json()["id"]
    suppression = client.delete(
        f"/api/v1/mesures/{mesure_id}",
        headers=entetes(token),
    )
    consultation = client.get(
        f"/api/v1/mesures/{mesure_id}",
        headers=entetes(token),
    )

    assert suppression.status_code == 204
    assert consultation.status_code == 404


def test_supprimer_mesure_interdit_accueil(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)
    creation = creer_mesure(client, client_id, token)

    response = client.delete(
        f"/api/v1/mesures/{creation.json()['id']}",
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 403


def test_supprimer_mesure_inexistante(client, utilisateurs_test):
    response = client.delete(
        "/api/v1/mesures/999999",
        headers=entetes(utilisateurs_test["tailleur"]),
    )

    assert response.status_code == 404


def test_supprimer_mesure_liee_a_commande(
    client,
    db,
    utilisateurs_test,
):
    token = utilisateurs_test["tailleur"]
    client_id = creer_client(client, token)
    creation = creer_mesure(client, client_id, token)
    mesure_id = creation.json()["id"]

    tailleur = db.scalar(
        select(Utilisateur).where(
            Utilisateur.email == "tailleur@example.com"
        )
    )

    commande = Commande(
        numero="CMD-TEST-MESURE",
        client_id=client_id,
        mesure_id=mesure_id,
        date_livraison_prevue=date.today(),
        cree_par_id=tailleur.id,
    )
    db.add(commande)
    db.commit()

    response = client.delete(
        f"/api/v1/mesures/{mesure_id}",
        headers=entetes(token),
    )

    assert response.status_code == 409


