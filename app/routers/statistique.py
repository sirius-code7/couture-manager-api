from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import exiger_roles
from app.models.utilisateur import Utilisateur
from app.schemas.statistique import (
    ChiffreAffairesRead,
    ImpayesRead,
    TableauBordRead,
    TopClientRead,
    TypeVetementStatistiqueRead,
)
from app.services.statistique import (
    obtenir_chiffre_affaires,
    obtenir_impayes,
    obtenir_statistiques_types_vetement,
    obtenir_tableau_de_bord,
    obtenir_top_clients,
)


router = APIRouter(
    prefix="/api/v1/statistiques",
    tags=["Statistiques"],
    dependencies=[Depends(get_current_user)],
)


def definir_periode(
    date_debut: date | None,
    date_fin: date | None,
) -> tuple[date, date]:
    aujourd_hui = date.today()

    if date_fin is None:
        date_fin = aujourd_hui

    if date_debut is None:
        date_debut = date_fin.replace(day=1)

    if date_debut > date_fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La date de début doit précéder la date de fin.",
        )

    return date_debut, date_fin


@router.get(
    "/tableau-de-bord",
    response_model=TableauBordRead,
)
def lire_tableau_de_bord(
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin")),
):
    return obtenir_tableau_de_bord(db)


@router.get(
    "/chiffre-affaires",
    response_model=ChiffreAffairesRead,
)
def lire_chiffre_affaires(
    granularite: str = Query(default="jour", pattern="^(jour|mois)$"),
    date_debut: date | None = Query(default=None),
    date_fin: date | None = Query(default=None),
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin")),
):
    debut, fin = definir_periode(date_debut, date_fin)

    return obtenir_chiffre_affaires(
        db=db,
        granularite=granularite,
        date_debut=debut,
        date_fin=fin,
    )


@router.get(
    "/types-vetement",
    response_model=list[TypeVetementStatistiqueRead],
)
def lire_statistiques_types_vetement(
    date_debut: date | None = Query(default=None),
    date_fin: date | None = Query(default=None),
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin")),
):
    debut, fin = definir_periode(date_debut, date_fin)

    return obtenir_statistiques_types_vetement(
        db=db,
        date_debut=debut,
        date_fin=fin,
    )


@router.get(
    "/top-clients",
    response_model=list[TopClientRead],
)
def lire_top_clients(
    date_debut: date | None = Query(default=None),
    date_fin: date | None = Query(default=None),
    limite: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin")),
):
    debut, fin = definir_periode(date_debut, date_fin)

    return obtenir_top_clients(
        db=db,
        date_debut=debut,
        date_fin=fin,
        limite=limite,
    )


@router.get(
    "/impayes",
    response_model=ImpayesRead,
)
def lire_impayes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(exiger_roles("admin")),
):
    return obtenir_impayes(
        db=db,
        limit=limit,
        offset=offset,
    )