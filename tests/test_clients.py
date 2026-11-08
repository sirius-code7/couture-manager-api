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


def entetes(token):
    return {"Authorization": f"Bearer {token}"}


def test_creation_client(client, utilisateurs_test):
    response = client.post(
        "/clients",
        json=donnees_client("77 123-45-67"),
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 201
    assert response.json()["telephone"] == "771234567"
    assert response.json()["nom"] == "Diop"


def test_creation_client_sans_authentification(client):
    response = client.post("/clients", json=donnees_client())

    assert response.status_code == 401


def test_creation_client_telephone_deja_utilise(
    client,
    utilisateurs_test,
):
    headers = entetes(utilisateurs_test["accueil"])

    premiere_reponse = client.post(
        "/clients",
        json=donnees_client(),
        headers=headers,
    )

    deuxieme_reponse = client.post(
        "/clients",
        json=donnees_client("77-123-45-67"),
        headers=headers,
    )

    assert premiere_reponse.status_code == 201
    assert deuxieme_reponse.status_code == 409


def test_creation_client_telephone_invalide(
    client,
    utilisateurs_test,
):
    response = client.post(
        "/clients",
        json=donnees_client("77ABC4567"),
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 422


def test_consulter_client(client, utilisateurs_test):
    headers = entetes(utilisateurs_test["accueil"])

    creation = client.post(
        "/clients",
        json=donnees_client(),
        headers=headers,
    )

    client_id = creation.json()["id"]

    response = client.get(
        f"/clients/{client_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == client_id
    assert response.json()["prenom"] == "Mamadou"


def test_consulter_client_inexistant(client, utilisateurs_test):
    response = client.get(
        "/clients/999999",
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 404


def test_lister_clients_avec_pagination(client, utilisateurs_test):
    headers = entetes(utilisateurs_test["accueil"])

    for telephone in ("771111111", "772222222", "773333333"):
        response = client.post(
            "/clients",
            json=donnees_client(telephone),
            headers=headers,
        )
        assert response.status_code == 201

    response = client.get(
        "/clients?limit=2&offset=1",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 2
    assert response.json()["limit"] == 2
    assert response.json()["offset"] == 1


def test_modifier_client(client, utilisateurs_test):
    headers = entetes(utilisateurs_test["accueil"])

    creation = client.post(
        "/clients",
        json=donnees_client(),
        headers=headers,
    )

    client_id = creation.json()["id"]

    response = client.patch(
        f"/clients/{client_id}",
        json={
            "prenom": "Abdou",
            "telephone": "78 123-45-67",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["prenom"] == "Abdou"
    assert response.json()["telephone"] == "781234567"


def test_modifier_client_avec_telephone_deja_utilise(
    client,
    utilisateurs_test,
):
    headers = entetes(utilisateurs_test["accueil"])

    premier = client.post(
        "/clients",
        json=donnees_client("771111111"),
        headers=headers,
    )

    deuxieme = client.post(
        "/clients",
        json=donnees_client("772222222"),
        headers=headers,
    )

    response = client.patch(
        f"/clients/{deuxieme.json()['id']}",
        json={"telephone": "771111111"},
        headers=headers,
    )

    assert premier.status_code == 201
    assert deuxieme.status_code == 201
    assert response.status_code == 409


def test_modifier_client_inexistant(client, utilisateurs_test):
    response = client.patch(
        "/clients/999999",
        json={"prenom": "Abdou"},
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 404


def test_supprimer_client_interdit_accueil(
    client,
    utilisateurs_test,
):
    headers_accueil = entetes(utilisateurs_test["accueil"])

    creation = client.post(
        "/clients",
        json=donnees_client(),
        headers=headers_accueil,
    )

    response = client.delete(
        f"/clients/{creation.json()['id']}",
        headers=headers_accueil,
    )

    assert creation.status_code == 201
    assert response.status_code == 403


def test_supprimer_client_admin(client, utilisateurs_test):
    headers = entetes(utilisateurs_test["admin"])

    creation = client.post(
        "/clients",
        json=donnees_client(),
        headers=headers,
    )

    client_id = creation.json()["id"]

    suppression = client.delete(
        f"/clients/{client_id}",
        headers=headers,
    )

    consultation = client.get(
        f"/clients/{client_id}",
        headers=headers,
    )

    assert suppression.status_code == 204
    assert consultation.status_code == 404


def test_supprimer_client_inexistant(client, utilisateurs_test):
    response = client.delete(
        "/clients/999999",
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404
