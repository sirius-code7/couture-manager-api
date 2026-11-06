from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import exiger_roles
from app.schemas.type_vetement import (
    TypeVetementCreate,
    TypeVetementRead,
    TypeVetementUpdate,
)
from app.services.type_vetement import (
    NomTypeVetementDejaUtiliseError,
    creer_type_vetement,
    lister_types_vetement,
    modifier_type_vetement,
    obtenir_type_vetement_par_id,
)


router = APIRouter(
    prefix="/catalogue",
    tags=["Catalogue"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=TypeVetementRead,
    status_code=status.HTTP_201_CREATED,
)
def creer_nouvelle_prestation(
    donnees: TypeVetementCreate,
    db: Session = Depends(get_db),
    _=Depends(exiger_roles("admin")),
):
    """Ajoute une prestation au catalogue."""

    try:
        return creer_type_vetement(db, donnees)
    except NomTypeVetementDejaUtiliseError as erreur:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erreur),
        )


@router.get(
    "",
    response_model=list[TypeVetementRead],
)
def lister_le_catalogue(
    actifs_seulement: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """Liste les prestations disponibles."""

    return lister_types_vetement(
        db,
        actifs_seulement,
    )


@router.get(
    "/{type_vetement_id}",
    response_model=TypeVetementRead,
)
def consulter_une_prestation(
    type_vetement_id: int,
    db: Session = Depends(get_db),
):
    """Retourne le détail d'une prestation."""

    prestation = obtenir_type_vetement_par_id(
        db,
        type_vetement_id,
    )

    if prestation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prestation introuvable.",
        )

    return prestation


@router.patch(
    "/{type_vetement_id}",
    response_model=TypeVetementRead,
)
def modifier_une_prestation(
    type_vetement_id: int,
    donnees: TypeVetementUpdate,
    db: Session = Depends(get_db),
    _=Depends(exiger_roles("admin")),
):
    """Modifie une prestation existante."""

    try:
        prestation = modifier_type_vetement(
            db,
            type_vetement_id,
            donnees,
        )
    except NomTypeVetementDejaUtiliseError as erreur:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erreur),
        )

    if prestation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prestation introuvable.",
        )

    return prestation