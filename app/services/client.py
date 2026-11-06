from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.client import ClientCreate

from sqlalchemy.exc import IntegrityError

from sqlalchemy import func, select

from app.schemas.client import ClientCreate, ClientUpdate


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

def lister_clients(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Client], int]:
    """Retourne une page de clients et le nombre total."""

    total = db.scalar(select(func.count()).select_from(Client)) or 0

    clients = db.scalars(
        select(Client)
        .order_by(Client.id)
        .limit(limit)
        .offset(offset)
    ).all()

    return list(clients), total

def modifier_client(
    db: Session,
    client_id: int,
    donnees: ClientUpdate,
) -> Client | None:
    """Modifie un client existant."""

    client = db.get(Client, client_id)

    if client is None:
        return None

    modifications = donnees.model_dump(exclude_unset=True)

    if "telephone" in modifications and modifications["telephone"] is not None:
        telephone_existant = db.scalar(
            select(Client).where(
                Client.telephone == modifications["telephone"],
                Client.id != client_id,
            )
        )

        if telephone_existant is not None:
            raise TelephoneDejaUtiliseError

    for champ, valeur in modifications.items():
        setattr(client, champ, valeur)

    try:
        db.commit()
        db.refresh(client)
    except IntegrityError as erreur:
        db.rollback()

        if "telephone" in modifications and modifications["telephone"] is not None:
            telephone_existant = db.scalar(
                select(Client).where(
                    Client.telephone == modifications["telephone"],
                    Client.id != client_id,
                )
            )

            if telephone_existant is not None:
                raise TelephoneDejaUtiliseError from erreur

        raise

    return client

