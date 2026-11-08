from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import exiger_roles
from app.models.utilisateur import Utilisateur
from app.schemas.mesure import MesureCreate, MesureRead, MesureUpdate
from app.services.mesure import (
    ClientIntrouvableError,
    MesureIntrouvableError,
    MesureInvalideError,
    MesureLieeACommandeError,
    creer_mesure,
    lister_mesures_client,
    modifier_mesure,
    obtenir_derniere_mesure,
    obtenir_mesure,
    supprimer_mesure,
)

router = APIRouter(
    tags=["Mesures"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/clients/{client_id}/mesures",
    response_model=MesureRead,
    status_code=status.HTTP_201_CREATED,
)
def creer_une_mesure(
    client_id: int,
    donnees: MesureCreate,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("tailleur")),
):
    try:
        return creer_mesure(db, client_id, utilisateur.id, donnees)
    except ClientIntrouvableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable.",
        )


@router.get(
    "/clients/{client_id}/mesures",
    response_model=list[MesureRead],
)
def lister_les_mesures(
    client_id: int,
    db: Session = Depends(get_db),
):
    try:
        return lister_mesures_client(db, client_id)
    except ClientIntrouvableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable.",
        )


@router.get(
    "/clients/{client_id}/mesures/derniere",
    response_model=MesureRead,
)
def lire_la_derniere_mesure(
    client_id: int,
    db: Session = Depends(get_db),
):
    try:
        return obtenir_derniere_mesure(db, client_id)
    except ClientIntrouvableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable.",
        )
    except MesureIntrouvableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune mesure enregistrée pour ce client.",
        )


@router.get(
    "/mesures/{mesure_id}",
    response_model=MesureRead,
)
def lire_une_mesure(
    mesure_id: int,
    db: Session = Depends(get_db),
):
    try:
        return obtenir_mesure(db, mesure_id)
    except MesureIntrouvableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesure introuvable.",
        )


@router.patch(
    "/mesures/{mesure_id}",
    response_model=MesureRead,
)
def modifier_une_mesure(
    mesure_id: int,
    donnees: MesureUpdate,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("tailleur")),
):
    try:
        return modifier_mesure(db, mesure_id, donnees)
    except MesureIntrouvableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesure introuvable.",
        )
    except MesureInvalideError as erreur:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erreur),
        )


@router.delete(
    "/mesures/{mesure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def supprimer_une_mesure(
    mesure_id: int,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("tailleur")),
):
    try:
        supprimer_mesure(db, mesure_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except MesureIntrouvableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesure introuvable.",
        )
    except MesureLieeACommandeError as erreur:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erreur),
        )
