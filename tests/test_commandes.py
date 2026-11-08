import pytest


def entetes(token):
    return {"Authorization": f"Bearer {token}"}


def donnees_client():
    return {
        "nom": "Diop",
        "prenom": "Mamadou",
        "telephone": "771234567",
        "email": "mamadou@example.com",
        "adresse": "Dakar, Senegal",
        "genre": "homme",
        "notes": "Client de test",
    }


def donnees_prestation(nom="Boubou commande test"):
    return {
        "nom": nom,
        "description": "Boubou homme sur mesure",
        "prix_base": 35000,
        "delai_jours": 10,
    }


def creer_ressources(
    client,
    token,
    nom_prestation="Boubou commande test",
    telephone="771234567",
):
    donnees = donnees_client()
    donnees["telephone"] = telephone

    reponse_client = client.post(
        "/clients",
        json=donnees,
        headers=entetes(token),
    )

    reponse_prestation = client.post(
        "/catalogue",
        json=donnees_prestation(nom_prestation),
        headers=entetes(token),
    )

    assert reponse_client.status_code == 201
    assert reponse_prestation.status_code == 201

    return reponse_client.json()["id"], reponse_prestation.json()["id"]


def donnees_commande(client_id, prestation_id):
    return {
        "client_id": client_id,
        "remise": 0,
        "notes": "Commande de test",
        "lignes": [
            {
                "type_vetement_id": prestation_id,
                "description": "Boubou bleu",
                "quantite": 2,
            }
        ],
    }


def creer_commande(
    client,
    token,
    nom_prestation="Boubou commande test",
    admin_token=None,
):
    token_preparation = admin_token or token

    client_id, prestation_id = creer_ressources(
        client,
        token_preparation,
        nom_prestation,
    )

    return client.post(
        "/commandes",
        json=donnees_commande(client_id, prestation_id),
        headers=entetes(token),
    )


def test_creation_commande_admin(client, utilisateurs_test):
    response = creer_commande(
        client,
        utilisateurs_test["admin"],
    )

    assert response.status_code == 201
    assert response.json()["statut"] == "en_attente"
    assert response.json()["montant_total"] == 70000
    assert response.json()["montant_paye"] == 0
    assert response.json()["numero"].startswith("CMD-")


def test_creation_commande_accueil(client, utilisateurs_test):
    response = creer_commande(
        client,
        utilisateurs_test["accueil"],
        admin_token=utilisateurs_test["admin"],
    )

    assert response.status_code == 201


def test_creation_commande_interdite_tailleur(
    client,
    utilisateurs_test,
):
    response = creer_commande(
        client,
        utilisateurs_test["tailleur"],
        admin_token=utilisateurs_test["admin"],
    )

    assert response.status_code == 403


def test_creation_commande_sans_authentification(client):
    response = client.post(
        "/commandes",
        json={},
    )

    assert response.status_code == 401


def test_creation_commande_sans_ligne(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    client_id, prestation_id = creer_ressources(client, token)

    donnees = donnees_commande(client_id, prestation_id)
    donnees["lignes"] = []

    response = client.post(
        "/commandes",
        json=donnees,
        headers=entetes(token),
    )

    assert response.status_code == 422


def test_creation_commande_client_inexistant(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    _, prestation_id = creer_ressources(client, token)

    donnees = donnees_commande(999999, prestation_id)

    response = client.post(
        "/commandes",
        json=donnees,
        headers=entetes(token),
    )

    assert response.status_code == 404


def test_creation_commande_remise_superieure_au_total(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    client_id, prestation_id = creer_ressources(client, token)

    donnees = donnees_commande(client_id, prestation_id)
    donnees["remise"] = 100000

    response = client.post(
        "/commandes",
        json=donnees,
        headers=entetes(token),
    )

    assert response.status_code == 409


def test_lister_commandes_utilisateur_authentifie(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)

    response = client.get(
        "/commandes",
        headers=entetes(token),
    )

    assert creation.status_code == 201
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1


def test_lister_commandes_sans_authentification(client):
    response = client.get("/commandes")

    assert response.status_code == 401


def test_filtrer_commandes_par_statut(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)

    commande_id = creation.json()["id"]

    changement = client.post(
        f"/commandes/{commande_id}/statut",
        json={"statut": "en_coupe"},
        headers=entetes(token),
    )

    response = client.get(
        "/commandes?statut=en_coupe",
        headers=entetes(token),
    )

    assert changement.status_code == 200
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["statut"] == "en_coupe"


def test_consulter_commande(client, utilisateurs_test):
    token = utilisateurs_test["accueil"]
    creation = creer_commande(
        client,
        utilisateurs_test["admin"],
    )

    response = client.get(
        f"/commandes/{creation.json()['id']}",
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == creation.json()["id"]


def test_consulter_commande_inexistante(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/commandes/999999",
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404


def test_modifier_commande_admin(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)

    response = client.patch(
        f"/commandes/{creation.json()['id']}",
        json={"remise": 5000, "notes": "Remise accordee"},
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["remise"] == 5000
    assert response.json()["montant_total"] == 65000


def test_modifier_commande_interdit_tailleur(
    client,
    utilisateurs_test,
):
    creation = creer_commande(
        client,
        utilisateurs_test["admin"],
    )

    response = client.patch(
        f"/commandes/{creation.json()['id']}",
        json={"notes": "Modification"},
        headers=entetes(utilisateurs_test["tailleur"]),
    )

    assert response.status_code == 403


def test_modifier_commande_inexistante(
    client,
    utilisateurs_test,
):
    response = client.patch(
        "/commandes/999999",
        json={"notes": "Modification"},
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404


def test_changer_statut_commande(client, utilisateurs_test):
    token = utilisateurs_test["tailleur"]
    creation = creer_commande(
        client,
        utilisateurs_test["admin"],
    )

    response = client.post(
        f"/commandes/{creation.json()['id']}/statut",
        json={"statut": "en_coupe"},
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["statut"] == "en_coupe"


def test_transition_statut_invalide(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)

    response = client.post(
        f"/commandes/{creation.json()['id']}/statut",
        json={"statut": "terminee"},
        headers=entetes(token),
    )

    assert response.status_code == 409


def test_tailleur_ne_peut_pas_annuler_commande(
    client,
    utilisateurs_test,
):
    creation = creer_commande(
        client,
        utilisateurs_test["admin"],
    )

    response = client.post(
        f"/commandes/{creation.json()['id']}/statut",
        json={"statut": "annulee"},
        headers=entetes(utilisateurs_test["tailleur"]),
    )

    assert response.status_code == 403


def test_historique_commande(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)
    commande_id = creation.json()["id"]

    client.post(
        f"/commandes/{commande_id}/statut",
        json={"statut": "en_coupe"},
        headers=entetes(token),
    )

    response = client.get(
        f"/commandes/{commande_id}/historique",
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["nouveau_statut"] == "en_attente"
    assert response.json()[1]["nouveau_statut"] == "en_coupe"


def test_historique_commande_inexistante(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/commandes/999999/historique",
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404


def test_ajouter_ligne_commande(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)
    commande_id = creation.json()["id"]

    _, prestation_id = creer_ressources(
        client,
        token,
        "Chemise commande test",
        telephone="771234568",
    )

    response = client.post(
        f"/commandes/{commande_id}/lignes",
        json={
            "type_vetement_id": prestation_id,
            "description": "Chemise blanche",
            "quantite": 1,
        },
        headers=entetes(token),
    )

    assert response.status_code == 201
    assert response.json()["montant_total"] == 105000


def test_ajouter_ligne_commande_inexistante(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    _, prestation_id = creer_ressources(client, token)

    response = client.post(
        "/commandes/999999/lignes",
        json={"type_vetement_id": prestation_id, "quantite": 1},
        headers=entetes(token),
    )

    assert response.status_code == 404


def test_annuler_commande_sans_paiement(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)

    response = client.post(
        f"/commandes/{creation.json()['id']}/statut",
        json={"statut": "annulee"},
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["statut"] == "annulee"


@pytest.mark.parametrize(
    "donnees",
    [
        {"quantite": 0},
        {"quantite": -1},
        {"type_vetement_id": 0},
    ],
)
def test_ajouter_ligne_donnees_invalides(
    client,
    utilisateurs_test,
    donnees,
):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)
    commande_id = creation.json()["id"]

    ligne = {
        "type_vetement_id": 1,
        "description": "Ligne invalide",
        "quantite": 1,
    }
    ligne.update(donnees)

    response = client.post(
        f"/commandes/{commande_id}/lignes",
        json=ligne,
        headers=entetes(token),
    )

    assert response.status_code == 422

def test_modifier_commande_remise_nulle(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)
    commande_id = creation.json()["id"]

    response = client.patch(
        f"/commandes/{commande_id}",
        json={"remise": None},
        headers=entetes(token),
    )

    assert response.status_code == 422


def test_annuler_commande_payee_sans_commentaire_remboursement(
    client,
    utilisateurs_test,
    db,
):
    from app.models.commande import Commande

    token = utilisateurs_test["admin"]
    creation = creer_commande(client, token)
    commande_id = creation.json()["id"]

    commande = db.get(Commande, commande_id)
    commande.montant_paye = 5000
    db.flush()

    response = client.post(
        f"/commandes/{commande_id}/statut",
        json={"statut": "annulee"},
        headers=entetes(token),
    )

    assert response.status_code == 422

