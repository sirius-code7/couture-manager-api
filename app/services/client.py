from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.client import ClientCreate

from sqlalchemy.exc import IntegrityError


class TelephoneDejaUtiliseError(Exception):
    """Levée lorsqu'un téléphone est déjà utilisé."""


def creer_client(db: Session, donnees: ClientCreate) -> Client:
    """Crée un client si son téléphone est disponible."""

    telephone_existant = db.scalar(
        select(Client).where(Client.telephone == donnees.telephone)
    )

    if telephone_existant is not None:
        raise TelephoneDejaUtiliseError

    client = Client(**donnees.model_dump())

    db.add(client)

    try:
        db.commit()
        db.refresh(client)
    except IntegrityError as erreur:
        db.rollback()
        raise TelephoneDejaUtiliseError from erreur

    return client


def obtenir_client_par_id(
    db: Session,
    client_id: int,
) -> Client | None:
    """Retourne un client ou None s'il n'existe pas."""

    return db.get(Client, client_id)