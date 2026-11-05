import secrets

from app.database.session import SessionLocal
from app.schemas.client import ClientCreate
from app.services.client import (
    TelephoneDejaUtiliseError,
    creer_client,
    obtenir_client_par_id,
)

db = SessionLocal()
client = None

try:
    # numéro unique pour pouvoir relancer le test
    telephone = f"77{secrets.randbelow(10**7):07d}"

    donnees = ClientCreate(
        nom="Diop",
        prenom="Fatou",
        telephone=telephone,
        genre="femme",
    )

    client = creer_client(db, donnees)

    print("1. Client créé :", client.id)
    print("2. Téléphone enregistré :", client.telephone)

    client_trouve = obtenir_client_par_id(db, client.id)

    print(
        "3. Client retrouvé :",
        client_trouve is not None and client_trouve.id == client.id,
    )

    try:
        creer_client(db, donnees)
    except TelephoneDejaUtiliseError:
        print("4. Doublon téléphone refusé : True")

finally:
    # nettoyage du client de test
    if client is not None:
        client_a_supprimer = db.get(type(client), client.id)

        if client_a_supprimer is not None:
            db.delete(client_a_supprimer)
            db.commit()

    db.close()