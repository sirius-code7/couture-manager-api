from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import exiger_roles
from app.models.utilisateur import Utilisateur
from app.schemas.paiement import PaiementCreate, PaiementRead
from app.services.paiement import (
    CommandePaiementIntrouvableError,
    PaiementImpossibleError,
    PaiementIntrouvableError,
    enregistrer_paiement,
    lister_paiements_commande,
    supprimer_paiement,
)


router = APIRouter(
    tags=["Paiements"],
    dependencies=[Depends(get_current_user)],
)


def traiter_erreur_paiement(erreur: Exception):
    if isinstance(
        erreur,
        (CommandePaiementIntrouvableError, PaiementIntrouvableError),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erreur),
        )

    if isinstance(erreur, PaiementImpossibleError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erreur),
        )

    raise erreur


@router.post(
    "/commandes/{commande_id}/paiements",
    response_model=PaiementRead,
    status_code=status.HTTP_201_CREATED,
)
def enregistrer_un_paiement(
    commande_id: int,
    donnees: PaiementCreate,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(
        exiger_roles("admin", "accueil")
    ),
):
    try:
        return enregistrer_paiement(
            db=db,
            commande_id=commande_id,
            utilisateur_id=utilisateur.id,
            donnees=donnees,
        )
    except Exception as erreur:
        traiter_erreur_paiement(erreur)


@router.get(
    "/commandes/{commande_id}/paiements",
    response_model=list[PaiementRead],
)
def lister_les_paiements(
    commande_id: int,
    db: Session = Depends(get_db),
):
    try:
        return lister_paiements_commande(
            db=db,
            commande_id=commande_id,
        )
    except Exception as erreur:
        traiter_erreur_paiement(erreur)


@router.delete(
    "/paiements/{paiement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def supprimer_un_paiement(
    paiement_id: int,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(
        exiger_roles("admin")
    ),
):
    try:
        supprimer_paiement(
            db=db,
            paiement_id=paiement_id,
        )
    except Exception as erreur:
        traiter_erreur_paiement(erreur)