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


def donnees_prestation(nom="Boubou paiement test"):
    return {
        "nom": nom,
        "description": "Boubou homme sur mesure",
        "prix_base": 35000,
        "delai_jours": 10,
    }


def creer_commande(
    client,
    token,
    telephone="771234567",
    nom_prestation="Boubou paiement test",
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

    reponse_commande = client.post(
        "/commandes",
        json={
            "client_id": reponse_client.json()["id"],
            "remise": 0,
            "notes": "Commande pour test paiement",
            "lignes": [
                {
                    "type_vetement_id": reponse_prestation.json()["id"],
                    "description": "Boubou bleu",
                    "quantite": 2,
                }
            ],
        },
        headers=entetes(token),
    )

    assert reponse_commande.status_code == 201

    return reponse_commande.json()


def donnees_paiement(montant=20000):
    return {
        "montant": montant,
        "mode": "wave",
        "reference": "WAVE-TEST-001",
        "date_paiement": str(date.today()),
    }


def creer_paiement(
    client,
    token,
    montant=20000,
    telephone="771234567",
    nom_prestation="Boubou paiement test",
):
    commande = creer_commande(
        client,
        token,
        telephone=telephone,
        nom_prestation=nom_prestation,
    )

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(montant),
        headers=entetes(token),
    )

    assert response.status_code == 201

    return commande, response.json()


def test_enregistrer_paiement_admin(client, utilisateurs_test):
    token = utilisateurs_test["admin"]

    commande = creer_commande(client, token)

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(),
        headers=entetes(token),
    )

    assert response.status_code == 201

    paiement = response.json()
    assert paiement["commande_id"] == commande["id"]
    assert paiement["montant"] == 20000
    assert paiement["mode"] == "wave"
    assert paiement["reference"] == "WAVE-TEST-001"


def test_enregistrer_paiement_accueil(client, utilisateurs_test):
    commande = creer_commande(
        client,
        utilisateurs_test["admin"],
    )

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(),
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 201


def test_enregistrer_paiement_interdit_tailleur(
    client,
    utilisateurs_test,
):
    commande = creer_commande(
        client,
        utilisateurs_test["admin"],
    )

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(),
        headers=entetes(utilisateurs_test["tailleur"]),
    )

    assert response.status_code == 403


def test_enregistrer_paiement_sans_authentification(
    client,
    utilisateurs_test,
):
    commande = creer_commande(
        client,
        utilisateurs_test["admin"],
    )

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(),
    )

    assert response.status_code == 401


def test_enregistrer_paiement_commande_inexistante(
    client,
    utilisateurs_test,
):
    response = client.post(
        "/commandes/999999/paiements",
        json=donnees_paiement(),
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404


def test_enregistrer_paiement_superieur_au_solde(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(100000),
        headers=entetes(token),
    )

    assert response.status_code == 409


def test_enregistrer_paiement_montant_restant_exact(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(70000),
        headers=entetes(token),
    )

    assert response.status_code == 201


def test_enregistrer_paiement_donnees_invalides(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    donnees_invalides = [
        {
            "montant": 0,
            "mode": "wave",
        },
        {
            "montant": -1000,
            "mode": "wave",
        },
        {
            "montant": 1000,
            "mode": "bitcoin",
        },
        {
            "montant": 1000,
            "mode": "wave",
            "date_paiement": str(date.today() + timedelta(days=1)),
        },
    ]

    for donnees in donnees_invalides:
        response = client.post(
            f"/commandes/{commande['id']}/paiements",
            json=donnees,
            headers=entetes(token),
        )

        assert response.status_code == 422


def test_enregistrer_paiement_met_a_jour_montant_paye(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]
    commande = creer_commande(client, token)

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(20000),
        headers=entetes(token),
    )

    assert response.status_code == 201

    response_commande = client.get(
        f"/commandes/{commande['id']}",
        headers=entetes(token),
    )

    assert response_commande.status_code == 200
    assert response_commande.json()["montant_paye"] == 20000


def test_lister_paiements_commande(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]

    commande, _ = creer_paiement(
        client,
        token,
        montant=20000,
    )

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json={
            "montant": 10000,
            "mode": "especes",
        },
        headers=entetes(token),
    )

    assert response.status_code == 201

    response = client.get(
        f"/commandes/{commande['id']}/paiements",
        headers=entetes(utilisateurs_test["tailleur"]),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_lister_paiements_commande_inexistante(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/commandes/999999/paiements",
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404


def test_lister_paiements_sans_authentification(
    client,
):
    response = client.get(
        "/commandes/999999/paiements",
    )

    assert response.status_code == 401


def test_supprimer_paiement_admin(client, utilisateurs_test):
    token = utilisateurs_test["admin"]

    _, paiement = creer_paiement(
        client,
        token,
    )

    response = client.delete(
        f"/paiements/{paiement['id']}",
        headers=entetes(token),
    )

    assert response.status_code == 204


def test_supprimer_paiement_interdit_accueil(
    client,
    utilisateurs_test,
):
    _, paiement = creer_paiement(
        client,
        utilisateurs_test["admin"],
    )

    response = client.delete(
        f"/paiements/{paiement['id']}",
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 403


def test_supprimer_paiement_interdit_tailleur(
    client,
    utilisateurs_test,
):
    _, paiement = creer_paiement(
        client,
        utilisateurs_test["admin"],
    )

    response = client.delete(
        f"/paiements/{paiement['id']}",
        headers=entetes(utilisateurs_test["tailleur"]),
    )

    assert response.status_code == 403


def test_supprimer_paiement_inexistant(
    client,
    utilisateurs_test,
):
    response = client.delete(
        "/paiements/999999",
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404


def test_supprimer_paiement_recalcule_montant_paye(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]

    commande, premier_paiement = creer_paiement(
        client,
        token,
        montant=20000,
    )

    response = client.post(
        f"/commandes/{commande['id']}/paiements",
        json=donnees_paiement(10000),
        headers=entetes(token),
    )

    assert response.status_code == 201

    response = client.delete(
        f"/paiements/{premier_paiement['id']}",
        headers=entetes(token),
    )

    assert response.status_code == 204

    response_commande = client.get(
        f"/commandes/{commande['id']}",
        headers=entetes(token),
    )

    assert response_commande.status_code == 200
    assert response_commande.json()["montant_paye"] == 10000
