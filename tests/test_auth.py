
def test_connexion_reussie(client, utilisateurs_test):
    response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_connexion_identifiants_incorrects(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "mauvais_mot_de_passe",
        },
    )

    assert response.status_code == 401


def test_connexion_compte_inactif(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "inactif@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401


def test_profil_sans_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_profil_avec_token(client, utilisateurs_test):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {utilisateurs_test['admin']}"
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"


def test_profil_avec_token_invalide(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer faux_token"},
    )

    assert response.status_code == 401


def test_compte_inactif_refuse_meme_avec_token(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {utilisateurs_test['inactif']}"
        },
    )

    assert response.status_code == 403


def test_statistiques_accessibles_admin(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/api/v1/statistiques/tableau-de-bord",
        headers={
            "Authorization": f"Bearer {utilisateurs_test['admin']}"
        },
    )

    assert response.status_code == 200


def test_statistiques_interdites_accueil(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/api/v1/statistiques/tableau-de-bord",
        headers={
            "Authorization": f"Bearer {utilisateurs_test['accueil']}"
        },
    )

    assert response.status_code == 403

