
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.commande import Commande
from app.models.mesure import Mesure
from app.schemas.mesure import CHAMPS_MESURES, MesureCreate, MesureUpdate


class ClientIntrouvableError(Exception):
    pass


class MesureIntrouvableError(Exception):
    pass


class MesureInvalideError(Exception):
    pass


class MesureLieeACommandeError(Exception):
    pass


def creer_mesure(
    db: Session,
    client_id: int,
    prise_par_id: int,
    donnees: MesureCreate,
) -> Mesure:
    client = db.get(Client, client_id)

    if client is None:
        raise ClientIntrouvableError

    mesure = Mesure(
        client_id=client_id,
        prise_par_id=prise_par_id,
        **donnees.model_dump(),
    )

    try:
        db.add(mesure)
        db.commit()
        db.refresh(mesure)
        return mesure
    except Exception:
        db.rollback()
        raise


def obtenir_mesure(db: Session, mesure_id: int) -> Mesure:
    mesure = db.get(Mesure, mesure_id)

    if mesure is None:
        raise MesureIntrouvableError

    return mesure


def lister_mesures_client(db: Session, client_id: int) -> list[Mesure]:
    if db.get(Client, client_id) is None:
        raise ClientIntrouvableError

    requete = (
        select(Mesure)
        .where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
    )

    return list(db.scalars(requete).all())


def obtenir_derniere_mesure(db: Session, client_id: int) -> Mesure:
    if db.get(Client, client_id) is None:
        raise ClientIntrouvableError

    requete = (
        select(Mesure)
        .where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
        .limit(1)
    )

    mesure = db.scalar(requete)

    if mesure is None:
        raise MesureIntrouvableError

    return mesure


def modifier_mesure(
    db: Session,
    mesure_id: int,
    donnees: MesureUpdate,
) -> Mesure:
    mesure = obtenir_mesure(db, mesure_id)
    modifications = donnees.model_dump(exclude_unset=True)

    if "date_prise" in modifications and modifications["date_prise"] is None:
        raise MesureInvalideError(
            "La date de prise ne peut pas être vide."
        )

    valeurs_finales = {
        champ: modifications.get(champ, getattr(mesure, champ))
        for champ in CHAMPS_MESURES
    }

    if not any(valeur is not None for valeur in valeurs_finales.values()):
        raise MesureInvalideError(
            "Une prise doit conserver au moins une mesure renseignée."
        )

    for champ, valeur in modifications.items():
        setattr(mesure, champ, valeur)

    try:
        db.commit()
        db.refresh(mesure)
        return mesure
    except Exception:
        db.rollback()
        raise


def supprimer_mesure(db: Session, mesure_id: int) -> None:
    mesure = obtenir_mesure(db, mesure_id)

    commande_liee = db.scalar(
        select(Commande.id)
        .where(Commande.mesure_id == mesure_id)
        .limit(1)
    )

    if commande_liee is not None:
        raise MesureLieeACommandeError(
            "Cette mesure est associée à une commande et ne peut pas être supprimée."
        )

    # le contrôle des commandes liées sera ajouté avec le modèle Commande

    try:
        db.delete(mesure)
        db.commit()
    except Exception:
        db.rollback()
        raise
