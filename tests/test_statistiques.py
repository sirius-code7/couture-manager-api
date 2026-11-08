from datetime import date, timedelta


def entetes(token):
    return {"Authorization": f"Bearer {token}"}


def creer_commande(client, token):
    response_client = client.post(
        "/clients",
        json={
            "nom": "Diop",
            "prenom": "Mamadou",
            "telephone": "771234567",
            "email": "mamadou@example.com",
            "adresse": "Dakar, Senegal",
            "genre": "homme",
            "notes": "Client de test",
        },
        headers=entetes(token),
    )

    response_type = client.post(
        "/catalogue",
        json={
            "nom": "Boubou statistique test",
            "description": "Boubou homme sur mesure",
            "prix_base": 35000,
            "delai_jours": 10,
        },
        headers=entetes(token),
    )

    assert response_client.status_code == 201
    assert response_type.status_code == 201

    response_commande = client.post(
        "/commandes",
        json={
            "client_id": response_client.json()["id"],
            "remise": 0,
            "notes": "Commande statistique",
            "lignes": [
                {
                    "type_vetement_id": response_type.json()["id"],
                    "description": "Boubou bleu",
                    "quantite": 2,
                }
            ],
        },
        headers=entetes(token),
    )

    assert response_commande.status_code == 201

    return response_commande.json()


def creer_paiement(client, token, commande_id):
    return client.post(
        f"/commandes/{commande_id}/paiements",
        json={
            "montant": 20000,
            "mode": "wave",
            "reference": "WAVE-STAT-001",
            "date_paiement": str(date.today()),
        },
        headers=entetes(token),
    )


def test_tableau_de_bord_admin(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response_paiement = creer_paiement(
        client,
        token,
        commande["id"],
    )
    assert response_paiement.status_code == 201

    response = client.get(
        "/api/v1/statistiques/tableau-de-bord",
        headers=entetes(token),
    )

    assert response.status_code == 200

    donnees = response.json()

    assert donnees["chiffre_affaires_mois"] == 70000
    assert donnees["encaisse_mois"] == 20000
    assert donnees["nb_commandes_mois"] == 1
    assert donnees["reste_a_encaisser"] == 50000
    assert donnees["commandes_par_statut"]["en_attente"] == 1


def test_chiffre_affaires_par_jour(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response_paiement = creer_paiement(
        client,
        token,
        commande["id"],
    )
    assert response_paiement.status_code == 201

    response = client.get(
        "/api/v1/statistiques/chiffre-affaires",
        params={
            "granularite": "jour",
            "date_debut": str(date.today()),
            "date_fin": str(date.today()),
        },
        headers=entetes(token),
    )

    assert response.status_code == 200

    donnees = response.json()

    assert donnees["granularite"] == "jour"
    assert donnees["date_debut"] == str(date.today())
    assert donnees["date_fin"] == str(date.today())
    assert len(donnees["items"]) == 1
    assert donnees["items"][0]["chiffre_affaires"] == 70000
    assert donnees["items"][0]["encaisse"] == 20000


def test_chiffre_affaires_par_mois(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    creer_commande(client, token)

    response = client.get(
        "/api/v1/statistiques/chiffre-affaires",
        params={"granularite": "mois"},
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["granularite"] == "mois"
    assert len(response.json()["items"]) == 1


def test_chiffre_affaires_granularite_invalide(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/api/v1/statistiques/chiffre-affaires",
        params={"granularite": "annee"},
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 422


def test_chiffre_affaires_periode_invalide(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/api/v1/statistiques/chiffre-affaires",
        params={
            "date_debut": str(date.today()),
            "date_fin": str(date.today() - timedelta(days=1)),
        },
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 422


def test_statistiques_types_vetement(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    creer_commande(client, token)

    response = client.get(
        "/api/v1/statistiques/types-vetement",
        params={
            "date_debut": str(date.today()),
            "date_fin": str(date.today()),
        },
        headers=entetes(token),
    )

    assert response.status_code == 200

    donnees = response.json()

    assert len(donnees) == 1
    assert donnees[0]["nom"] == "Boubou statistique test"
    assert donnees[0]["quantite"] == 2
    assert donnees[0]["chiffre_affaires"] == 70000


def test_top_clients(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    creer_commande(client, token)

    response = client.get(
        "/api/v1/statistiques/top-clients",
        headers=entetes(token),
    )

    assert response.status_code == 200

    donnees = response.json()

    assert len(donnees) == 1
    assert donnees[0]["nom"] == "Diop"
    assert donnees[0]["prenom"] == "Mamadou"
    assert donnees[0]["nb_commandes"] == 1
    assert donnees[0]["chiffre_affaires"] == 70000
    assert donnees[0]["solde_du"] == 70000


def test_top_clients_limite_invalide(client, utilisateurs_test):
    response = client.get(
        "/api/v1/statistiques/top-clients",
        params={"limite": 0},
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 422


def test_liste_impayes(client, utilisateurs_test):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response_paiement = creer_paiement(
        client,
        token,
        commande["id"],
    )
    assert response_paiement.status_code == 201

    response = client.get(
        "/api/v1/statistiques/impayes",
        headers=entetes(token),
    )

    assert response.status_code == 200

    donnees = response.json()

    assert donnees["total"] == 1
    assert donnees["limit"] == 20
    assert donnees["offset"] == 0
    assert len(donnees["items"]) == 1
    assert donnees["items"][0]["client_nom"] == "Mamadou Diop"
    assert donnees["items"][0]["montant_total"] == 70000
    assert donnees["items"][0]["montant_paye"] == 20000
    assert donnees["items"][0]["solde"] == 50000


def test_impayes_pagination_invalide(client, utilisateurs_test):
    response = client.get(
        "/api/v1/statistiques/impayes",
        params={"limit": 0},
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 422


def test_statistiques_interdites_accueil(client, utilisateurs_test):
    endpoints = [
        "/api/v1/statistiques/tableau-de-bord",
        "/api/v1/statistiques/chiffre-affaires",
        "/api/v1/statistiques/types-vetement",
        "/api/v1/statistiques/top-clients",
        "/api/v1/statistiques/impayes",
    ]

    for endpoint in endpoints:
        response = client.get(
            endpoint,
            headers=entetes(utilisateurs_test["accueil"]),
        )

        assert response.status_code == 403


def test_statistiques_interdites_tailleur(client, utilisateurs_test):
    endpoints = [
        "/api/v1/statistiques/tableau-de-bord",
        "/api/v1/statistiques/chiffre-affaires",
        "/api/v1/statistiques/types-vetement",
        "/api/v1/statistiques/top-clients",
        "/api/v1/statistiques/impayes",
    ]

    for endpoint in endpoints:
        response = client.get(
            endpoint,
            headers=entetes(utilisateurs_test["tailleur"]),
        )

        assert response.status_code == 403


def test_statistiques_sans_authentification(client):
    response = client.get(
        "/api/v1/statistiques/tableau-de-bord",
    )

    assert response.status_code == 401
