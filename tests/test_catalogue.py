import pytest


def donnees_prestation(nom="Boubou test"):
    return {
        "nom": nom,
        "description": "Boubou homme sur mesure",
        "prix_base": 35000,
        "delai_jours": 10,
    }


def entetes(token):
    return {"Authorization": f"Bearer {token}"}


def creer_prestation(client, token, nom="Boubou test"):
    return client.post(
        "/catalogue",
        json=donnees_prestation(nom),
        headers=entetes(token),
    )


def test_creation_prestation_admin(client, utilisateurs_test):
    response = creer_prestation(
        client,
        utilisateurs_test["admin"],
    )

    assert response.status_code == 201
    assert response.json()["nom"] == "Boubou test"
    assert response.json()["prix_base"] == 35000
    assert response.json()["actif"] is True


@pytest.mark.parametrize("role", ["accueil", "tailleur"])
def test_creation_prestation_interdite_aux_autres_roles(
    client,
    utilisateurs_test,
    role,
):
    response = creer_prestation(
        client,
        utilisateurs_test[role],
    )

    assert response.status_code == 403


def test_creation_prestation_sans_authentification(client):
    response = client.post(
        "/catalogue",
        json=donnees_prestation(),
    )

    assert response.status_code == 401


def test_creation_prestation_nom_deja_utilise(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]

    premiere = creer_prestation(client, token)
    deuxieme = creer_prestation(client, token)

    assert premiere.status_code == 201
    assert deuxieme.status_code == 409


@pytest.mark.parametrize(
    "modifications",
    [
        {"prix_base": 0},
        {"prix_base": -100},
        {"delai_jours": -1},
        {"nom": ""},
    ],
)
def test_creation_prestation_donnees_invalides(
    client,
    utilisateurs_test,
    modifications,
):
    donnees = donnees_prestation()
    donnees.update(modifications)

    response = client.post(
        "/catalogue",
        json=donnees,
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 422


def test_lister_catalogue_utilisateur_authentifie(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/catalogue",
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_lister_catalogue_sans_authentification(client):
    response = client.get("/catalogue")

    assert response.status_code == 401


def test_catalogue_filtre_les_prestations_inactives(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]

    creation = creer_prestation(
        client,
        token,
        "Prestation inactive test",
    )

    prestation_id = creation.json()["id"]

    desactivation = client.patch(
        f"/catalogue/{prestation_id}",
        json={"actif": False},
        headers=entetes(token),
    )

    actifs = client.get(
        "/catalogue",
        headers=entetes(token),
    )

    tous = client.get(
        "/catalogue?actifs_seulement=false",
        headers=entetes(token),
    )

    noms_actifs = [item["nom"] for item in actifs.json()]
    noms_tous = [item["nom"] for item in tous.json()]

    assert desactivation.status_code == 200
    assert "Prestation inactive test" not in noms_actifs
    assert "Prestation inactive test" in noms_tous


def test_consulter_prestation(client, utilisateurs_test):
    token = utilisateurs_test["accueil"]

    creation = creer_prestation(
        client,
        utilisateurs_test["admin"],
    )

    response = client.get(
        f"/catalogue/{creation.json()['id']}",
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["nom"] == "Boubou test"


def test_consulter_prestation_inexistante(
    client,
    utilisateurs_test,
):
    response = client.get(
        "/catalogue/999999",
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404


def test_modifier_prestation_admin(client, utilisateurs_test):
    token = utilisateurs_test["admin"]

    creation = creer_prestation(client, token)
    prestation_id = creation.json()["id"]

    response = client.patch(
        f"/catalogue/{prestation_id}",
        json={
            "prix_base": 40000,
            "delai_jours": 12,
        },
        headers=entetes(token),
    )

    assert response.status_code == 200
    assert response.json()["prix_base"] == 40000
    assert response.json()["delai_jours"] == 12


def test_modifier_prestation_interdit_accueil(
    client,
    utilisateurs_test,
):
    creation = creer_prestation(
        client,
        utilisateurs_test["admin"],
    )

    response = client.patch(
        f"/catalogue/{creation.json()['id']}",
        json={"prix_base": 40000},
        headers=entetes(utilisateurs_test["accueil"]),
    )

    assert response.status_code == 403


def test_modifier_prestation_nom_deja_utilise(
    client,
    utilisateurs_test,
):
    token = utilisateurs_test["admin"]

    premiere = creer_prestation(client, token, "Boubou test A")
    deuxieme = creer_prestation(client, token, "Boubou test B")

    response = client.patch(
        f"/catalogue/{deuxieme.json()['id']}",
        json={"nom": "Boubou test A"},
        headers=entetes(token),
    )

    assert premiere.status_code == 201
    assert deuxieme.status_code == 201
    assert response.status_code == 409


def test_modifier_prestation_inexistante(
    client,
    utilisateurs_test,
):
    response = client.patch(
        "/catalogue/999999",
        json={"prix_base": 40000},
        headers=entetes(utilisateurs_test["admin"]),
    )

    assert response.status_code == 404
