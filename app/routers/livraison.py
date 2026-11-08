from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import exiger_roles
from app.models.utilisateur import Utilisateur
from app.schemas.livraison import (
    LivraisonConfirmer,
    LivraisonPlanifier,
    LivraisonRead,
    LivraisonTourneeRead,
)
from app.services.livraison import (
    CommandeLivraisonIntrouvableError,
    LivraisonImpossibleError,
    LivraisonIntrouvableError,
    confirmer_livraison,
    lister_livraisons,
    obtenir_livraison,
    planifier_livraison,
)

router = APIRouter(
    tags=["Livraisons"],
    dependencies=[Depends(get_current_user)],
)


def traiter_erreur_livraison(erreur: Exception):
    if isinstance(erreur, CommandeLivraisonIntrouvableError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erreur),
        )

    if isinstance(erreur, LivraisonIntrouvableError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erreur),
        )

    if isinstance(erreur, LivraisonImpossibleError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erreur),
        )

    raise erreur


@router.put(
    "/commandes/{commande_id}/livraison",
    response_model=LivraisonRead,
)
def planifier_ou_replanifier_livraison(
    commande_id: int,
    donnees: LivraisonPlanifier,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(
        exiger_roles("admin", "accueil")
    ),
):
    try:
        return planifier_livraison(
            db=db,
            commande_id=commande_id,
            donnees=donnees,
        )
    except Exception as erreur:
        traiter_erreur_livraison(erreur)


@router.get(
    "/commandes/{commande_id}/livraison",
    response_model=LivraisonRead,
)
def consulter_livraison(
    commande_id: int,
    db: Session = Depends(get_db),
):
    try:
        return obtenir_livraison(
            db=db,
            commande_id=commande_id,
        )
    except Exception as erreur:
        traiter_erreur_livraison(erreur)


@router.post(
    "/commandes/{commande_id}/livraison/confirmer",
    response_model=LivraisonRead,
)
def confirmer_une_livraison(
    commande_id: int,
    donnees: LivraisonConfirmer,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(
        exiger_roles("admin", "accueil")
    ),
):
    try:
        return confirmer_livraison(
            db=db,
            commande_id=commande_id,
            utilisateur_id=utilisateur.id,
            donnees=donnees,
        )
    except Exception as erreur:
        traiter_erreur_livraison(erreur)


@router.get(
    "/livraisons",
    response_model=list[LivraisonTourneeRead],
)
def consulter_la_tournee(
    statut: str | None = Query(
        default=None,
        pattern="^(planifiee|livree)$",
    ),
    date_min: date | None = None,
    date_max: date | None = None,
    db: Session = Depends(get_db),
):
    return lister_livraisons(
        db=db,
        statut=statut,
        date_min=date_min,
        date_max=date_max,
    )