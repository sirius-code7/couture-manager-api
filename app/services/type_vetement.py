from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.type_vetement import TypeVetement
from app.schemas.type_vetement import (
    TypeVetementCreate,
    TypeVetementUpdate,
)


class NomTypeVetementDejaUtiliseError(Exception):
    """Signale qu'un nom de prestation est déjà utilisé."""


def creer_type_vetement(
    db: Session,
    donnees: TypeVetementCreate,
) -> TypeVetement:
    """Crée une nouvelle prestation dans le catalogue."""

    prestation_existante = db.scalar(
        select(TypeVetement).where(
            TypeVetement.nom == donnees.nom
        )
    )

    if prestation_existante:
        raise NomTypeVetementDejaUtiliseError(
            "Cette prestation existe déjà."
        )

    prestation = TypeVetement(**donnees.model_dump())

    db.add(prestation)

    try:
        db.commit()
        db.refresh(prestation)
    except IntegrityError as erreur:
        db.rollback()
        raise NomTypeVetementDejaUtiliseError(
            "Cette prestation existe déjà."
        ) from erreur

    return prestation


def lister_types_vetement(
    db: Session,
    actifs_seulement: bool = True,
) -> list[TypeVetement]:
    """Liste les prestations du catalogue par ordre alphabétique."""

    requete = select(TypeVetement)

    if actifs_seulement:
        requete = requete.where(
            TypeVetement.actif.is_(True)
        )

    requete = requete.order_by(TypeVetement.nom)

    return list(db.scalars(requete).all())


def obtenir_type_vetement_par_id(
    db: Session,
    type_vetement_id: int,
) -> TypeVetement | None:
    """Retourne une prestation à partir de son identifiant."""

    return db.get(TypeVetement, type_vetement_id)


def modifier_type_vetement(
    db: Session,
    type_vetement_id: int,
    donnees: TypeVetementUpdate,
) -> TypeVetement | None:
    """Modifie uniquement les champs réellement envoyés."""

    prestation = obtenir_type_vetement_par_id(
        db,
        type_vetement_id,
    )

    if prestation is None:
        return None

    donnees_modifiees = donnees.model_dump(exclude_unset=True)

    if "nom" in donnees_modifiees:
        prestation_existante = db.scalar(
            select(TypeVetement).where(
                TypeVetement.nom == donnees_modifiees["nom"],
                TypeVetement.id != type_vetement_id,
            )
        )

        if prestation_existante:
            raise NomTypeVetementDejaUtiliseError(
                "Cette prestation existe déjà."
            )

    for champ, valeur in donnees_modifiees.items():
        setattr(prestation, champ, valeur)

    try:
        db.commit()
        db.refresh(prestation)
    except IntegrityError as erreur:
        db.rollback()
        raise NomTypeVetementDejaUtiliseError(
            "Cette prestation existe déjà."
        ) from erreur

    return prestation