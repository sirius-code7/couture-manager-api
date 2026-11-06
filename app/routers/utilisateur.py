from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import exiger_roles
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import (
    UtilisateurCreate,
    UtilisateurListResponse,
    UtilisateurRead,
    UtilisateurUpdate,
)
from app.services.utilisateur import (
    EmailDejaUtiliseError,
    ModificationUtilisateurInvalideError,
    creer_utilisateur,
    lister_utilisateurs,
    modifier_utilisateur,
    obtenir_utilisateur_par_id,
)


router = APIRouter(
    prefix="/utilisateurs",
    tags=["Utilisateurs"],
    dependencies=[Depends(exiger_roles("admin"))],
)


@router.post(
    "",
    response_model=UtilisateurRead,
    status_code=status.HTTP_201_CREATED,
)
def creer_nouvel_utilisateur(
    donnees: UtilisateurCreate,
    db: Session = Depends(get_db),
):
    try:
        return creer_utilisateur(db, donnees)
    except EmailDejaUtiliseError as erreur:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erreur),
        )


@router.get(
    "",
    response_model=UtilisateurListResponse,
)
def lister_tous_les_utilisateurs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    utilisateurs, total = lister_utilisateurs(db, limit, offset)

    return {
        "items": utilisateurs,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{utilisateur_id}",
    response_model=UtilisateurRead,
)
def consulter_utilisateur(
    utilisateur_id: int,
    db: Session = Depends(get_db),
):
    utilisateur = obtenir_utilisateur_par_id(db, utilisateur_id)

    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    return utilisateur


@router.patch(
    "/{utilisateur_id}",
    response_model=UtilisateurRead,
)
def modifier_un_utilisateur(
    utilisateur_id: int,
    donnees: UtilisateurUpdate,
    db: Session = Depends(get_db),
    utilisateur_connecte: Utilisateur = Depends(get_current_user),
):
    try:
        utilisateur = modifier_utilisateur(
            db,
            utilisateur_id,
            donnees,
            utilisateur_connecte,
        )
    except ModificationUtilisateurInvalideError as erreur:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erreur),
    )

    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    return utilisateur