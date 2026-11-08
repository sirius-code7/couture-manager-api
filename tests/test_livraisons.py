
from datetime import date, timedelta


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


def creer_commande(client, token, telephone="771234567"):
    donnees = donnees_client()
    donnees["telephone"] = telephone

    response_client = client.post(
        "/api/v1/clients",
        json=donnees,
        headers=entetes(token),
    )

    response_prestation = client.post(
        "/api/v1/catalogue",
        json={
            "nom": "Boubou livraison test",
            "description": "Boubou homme sur mesure",
            "prix_base": 35000,
            "delai_jours": 10,
        },
        headers=entetes(token),
    )

    assert response_client.status_code == 201
    assert response_prestation.status_code == 201

    response_commande = client.post(
        "/api/v1/commandes",
        json={
            "client_id": response_client.json()["id"],
            "remise": 0,
            "notes": "Commande pour test livraison",
            "lignes": [
                {
                    "type_vetement_id": response_prestation.json()["id"],
                    "description": "Boubou bleu",
                    "quantite": 2,
                }
            ],
        },
        headers=entetes(token),
    )

    assert response_commande.status_code == 201
    return response_commande.json()


def rendre_commande_terminee(client, commande_id, token):
    for statut in ("en_coupe", "en_couture", "terminee"):
        response = client.post(
            f"/api/v1/commandes/{commande_id}/statut",
            json={"statut": statut},
            headers=entetes(token),
        )
        assert response.status_code == 200


def planifier_livraison(client, commande_id, token, **modifications):
    donnees = {
        "mode": "retrait_atelier",
        "date_prevue": str(date.today() + timedelta(days=2)),
        "adresse": None,
        "livreur": None,
        "notes": "Livraison de test",
    }
    donnees.update(modifications)

    return client.put(
        f"/api/v1/commandes/{commande_id}/livraison",
        json=donnees,
        headers=entetes(token),
    )


def test_planifier_livraison_admin(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = planifier_livraison(
        client,
        commande["id"],
        token,
    )

    assert response.status_code == 200
    assert response.json()["commande_id"] == commande["id"]
    assert response.json()["mode"] == "retrait_atelier"
    assert response.json()["statut"] == "planifiee"


def test_planifier_livraison_accueil(client, utilisateurs_test):
    admin = utilisateurs_test["admin"]
    token = utilisateurs_test["accueil"]
    commande = creer_commande(client, admin)

    response = planifier_livraison(
        client,
        commande["id"],
        token,
    )

    assert response.status_code == 200


def test_planifier_livraison_interdit_tailleur(
    client,
    utilisateurs_test,
):
    admin = utilisateurs_test["admin"]
    commande = creer_commande(client, admin)

    response = planifier_livraison(
        client,
        commande["id"],
        utilisateurs_test["tailleur"],
    )

    assert response.status_code == 403


def test_planifier_livraison_sans_authentification(client, utilisateurs_test):
    commande = creer_commande(client, utilisateurs_test["admin"])

    response = client.put(
        f"/api/v1/commandes/{commande['id']}/livraison",
        json={
            "mode": "retrait_atelier",
            "date_prevue": str(date.today()),
        },
    )

    assert response.status_code == 401


def test_planifier_livraison_domicile_avec_adresse(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = planifier_livraison(
        client,
        commande["id"],
        token,
        mode="domicile",
        adresse="Parcelles Assainies, Dakar",
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "domicile"
    assert response.json()["adresse"] == "Parcelles Assainies, Dakar"


def test_planifier_livraison_domicile_sans_adresse(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = planifier_livraison(
        client,
        commande["id"],
        token,
        mode="domicile",
    )

    assert response.status_code == 422


def test_planifier_livraison_mode_invalide(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = planifier_livraison(
        client,
        commande["id"],
        token,
        mode="transport",
    )

    assert response.status_code == 422


def test_replanifier_livraison_existante(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    premiere = planifier_livraison(client, commande["id"], token)
    assert premiere.status_code == 200

    seconde = planifier_livraison(
        client,
        commande["id"],
        token,
        mode="domicile",
        adresse="MÃ©dina, Dakar",
    )

    assert seconde.status_code == 200
    assert seconde.json()["mode"] == "domicile"
    assert seconde.json()["adresse"] == "MÃ©dina, Dakar"


def test_planifier_livraison_commande_inexistante(
    client,
    utilisateurs_test,
):
    response = planifier_livraison(
        client,
        999999,
        utilisateurs_test["admin"],
    )

    assert response.status_code == 404


def test_planifier_livraison_commande_annulee(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    annulation = client.post(
        f"/api/v1/commandes/{commande['id']}/statut",
        json={"statut": "annulee"},
        headers=entetes(token),
    )
    assert annulation.status_code == 200

    response = planifier_livraison(client, commande["id"], token)

    assert response.status_code == 409


def test_obtenir_livraison_existante(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    planification = planifier_livraison(client, commande["id"], token)
    assert planification.status_code == 200

    response = client.get(
        f"/api/v1/commandes/{commande['id']}/livraison",
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["commande_id"] == commande["id"]


def test_obtenir_livraison_absente(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = client.get(
        f"/api/v1/commandes/{commande['id']}/livraison",
        headers=entetes(token),
    )

    assert response.status_code == 404


def test_obtenir_livraison_commande_inexistante(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/api/v1/commandes/999999/livraison",
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404


def test_confirmer_livraison_commande_non_terminee(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = client.post(
        f"/api/v1/commandes/{commande['id']}/livraison/confirmer",
        json={},
        headers=entetes(token),
    )

    assert response.status_code == 409


def test_confirmer_livraison_solde_impaye_interdit(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)
    rendre_commande_terminee(client, commande["id"], token)

    response = client.post(
        f"/api/v1/commandes/{commande['id']}/livraison/confirmer",
        json={},
        headers=entetes(token),
    )

    assert response.status_code == 409


def test_confirmer_livraison_solde_impaye_autorise(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)
    rendre_commande_terminee(client, commande["id"], token)

    response = client.post(
        f"/api/v1/commandes/{commande['id']}/livraison/confirmer",
        json={
            "autoriser_solde_impaye": True,
            "commentaire": "Livraison autorisÃ©e exceptionnellement.",
        },
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["statut"] == "livree"


def test_confirmer_livraison_commande_entierement_payee(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    paiement = client.post(
        f"/api/v1/commandes/{commande['id']}/paiements",
        json={
            "montant": commande["montant_total"],
            "mode": "wave",
            "reference": "WAVE-LIVRAISON-TEST",
            "date_paiement": str(date.today()),
        },
        headers=entetes(token),
    )
    assert paiement.status_code == 201

    rendre_commande_terminee(client, commande["id"], token)

    response = client.post(
        f"/api/v1/commandes/{commande['id']}/livraison/confirmer",
        json={},
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["statut"] == "livree"


def test_confirmer_livraison_interdit_tailleur(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)
    rendre_commande_terminee(client, commande["id"], token)

    response = client.post(
        f"/api/v1/commandes/{commande['id']}/livraison/confirmer",
        json={"autoriser_solde_impaye": True},
        headers=entetes(utilisateurs_test["tailleur"]),
    )

    assert response.status_code == 403


def test_confirmer_livraison_deja_livree(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)
    rendre_commande_terminee(client, commande["id"], token)

    premiere = client.post(
        f"/api/v1/commandes/{commande['id']}/livraison/confirmer",
        json={"autoriser_solde_impaye": True},
        headers=entetes(token),
    )
    assert premiere.status_code == 200

    seconde = client.post(
        f"/api/v1/commandes/{commande['id']}/livraison/confirmer",
        json={"autoriser_solde_impaye": True},
        headers=entetes(token),
    )

    assert seconde.status_code == 409


def test_lister_livraisons(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    planification = planifier_livraison(client, commande["id"], token)
    assert planification.status_code == 200

    response = client.get(
        "/api/v1/livraisons",
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert any(
        livraison["commande_id"] == commande["id"]
        for livraison in response.json()
    )


def test_lister_livraisons_filtre_statut(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    planifier_livraison(client, commande["id"], token)

    response = client.get(
        "/api/v1/livraisons",
        params={"statut": "planifiee"},
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert all(
        livraison["statut"] == "planifiee"
        for livraison in response.json()
    )


def test_lister_livraisons_sans_authentification(client):
    response = client.get("/api/v1/livraisons")

    assert response.status_code == 401


def test_lister_livraisons_filtre_statut_invalide(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/api/v1/livraisons",
        params={"statut": "en_attente"},
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 422

