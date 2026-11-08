from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import exiger_roles
from app.models.utilisateur import Utilisateur
from app.schemas.commande import (
    ChangementStatutCreate,
    CommandeCreate,
    CommandeListResponse,
    CommandeRead,
    CommandeUpdate,
    HistoriqueStatutRead,
    LigneCommandeCreate,
)
from app.services.commande import (
    ClientCommandeIntrouvableError,
    CommandeIntrouvableError,
    CommandeInvalideError,
    LigneCommandeIntrouvableError,
    MesureCommandeInvalideError,
    PrestationCommandeInvalideError,
    DonneesCommandeInvalidesError,
    ajouter_ligne_commande,
    changer_statut_commande,
    consulter_commande,
    creer_commande,
    lister_commandes,
    lister_historique_commande,
    modifier_commande,
    supprimer_ligne_commande,
)


router = APIRouter(
    prefix="/commandes",
    tags=["Commandes"],
    dependencies=[Depends(get_current_user)],
)


def traiter_erreur_commande(erreur: Exception):
    if isinstance(erreur, CommandeIntrouvableError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commande introuvable.",
        )

    if isinstance(erreur, LigneCommandeIntrouvableError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ligne de commande introuvable.",
        )

    if isinstance(erreur, ClientCommandeIntrouvableError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable.",
        )

    if isinstance(erreur, MesureCommandeInvalideError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erreur),
        )

    if isinstance(erreur, PrestationCommandeInvalideError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erreur),
        )

    if isinstance(erreur, DonneesCommandeInvalidesError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erreur),
    )

    if isinstance(erreur, CommandeInvalideError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(erreur),
        )

    raise erreur


@router.post(
    "",
    response_model=CommandeRead,
    status_code=status.HTTP_201_CREATED,
)
def creer_une_commande(
    donnees: CommandeCreate,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin", "accueil")),
):
    try:
        return creer_commande(db, utilisateur.id, donnees)
    except (
        ClientCommandeIntrouvableError,
        MesureCommandeInvalideError,
        PrestationCommandeInvalideError,
        CommandeInvalideError,
    ) as erreur:
        traiter_erreur_commande(erreur)


@router.get(
    "",
    response_model=CommandeListResponse,
)
def lister_les_commandes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    statut: Literal[
        "en_attente",
        "en_coupe",
        "en_couture",
        "essayage",
        "retouches",
        "terminee",
        "livree",
        "annulee",
    ] | None = None,
    client_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    commandes, total = lister_commandes(
        db,
        limit=limit,
        offset=offset,
        statut=statut,
        client_id=client_id,
    )

    return {
        "items": commandes,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{commande_id}",
    response_model=CommandeRead,
)
def consulter_une_commande(
    commande_id: int,
    db: Session = Depends(get_db),
):
    try:
        return consulter_commande(db, commande_id)
    except CommandeIntrouvableError as erreur:
        traiter_erreur_commande(erreur)


@router.patch(
    "/{commande_id}",
    response_model=CommandeRead,
)
def modifier_une_commande(
    commande_id: int,
    donnees: CommandeUpdate,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin", "accueil")),
):
    try:
        return modifier_commande(db, commande_id, donnees)
    except (
        CommandeIntrouvableError,
        DonneesCommandeInvalidesError,
        CommandeInvalideError,
    ) as erreur:
        traiter_erreur_commande(erreur)


@router.post(
    "/{commande_id}/statut",
    response_model=CommandeRead,
)
def modifier_le_statut_commande(
    commande_id: int,
    donnees: ChangementStatutCreate,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(
        exiger_roles("admin", "accueil", "tailleur")
    ),
):
    if utilisateur.role == "tailleur" and donnees.statut == "annulee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un tailleur ne peut pas annuler une commande.",
        )

    try:
        return changer_statut_commande(
            db,
            commande_id,
            utilisateur.id,
            donnees,
        )
    except (
        CommandeIntrouvableError,
        DonneesCommandeInvalidesError,
        CommandeInvalideError,
    ) as erreur:
        traiter_erreur_commande(erreur)


@router.get(
    "/{commande_id}/historique",
    response_model=list[HistoriqueStatutRead],
)
def consulter_historique_commande(
    commande_id: int,
    db: Session = Depends(get_db),
):
    try:
        return lister_historique_commande(db, commande_id)
    except CommandeIntrouvableError as erreur:
        traiter_erreur_commande(erreur)


@router.post(
    "/{commande_id}/lignes",
    response_model=CommandeRead,
    status_code=status.HTTP_201_CREATED,
)
def ajouter_une_ligne(
    commande_id: int,
    donnees: LigneCommandeCreate,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin", "accueil")),
):
    try:
        return ajouter_ligne_commande(db, commande_id, donnees)
    except (
        CommandeIntrouvableError,
        PrestationCommandeInvalideError,
        CommandeInvalideError,
    ) as erreur:
        traiter_erreur_commande(erreur)


@router.delete(
    "/lignes/{ligne_id}",
    response_model=CommandeRead,
)
def supprimer_une_ligne(
    ligne_id: int,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin", "accueil")),
):
    try:
        return supprimer_ligne_commande(db, ligne_id)
    except (
        CommandeIntrouvableError,
        LigneCommandeIntrouvableError,
        CommandeInvalideError,
    ) as erreur:
        traiter_erreur_commande(erreur)
