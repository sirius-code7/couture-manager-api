from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.client import Client
from app.schemas.client import (
    ClientCreate,
    ClientListResponse,
    ClientRead,
    ClientUpdate,
)
from app.services.client import (
    TelephoneDejaUtiliseError,
    creer_client,
    lister_clients,
    modifier_client,
    obtenir_client_par_id,
)

from fastapi import Query

from app.schemas.client import ClientCreate, ClientListResponse, ClientRead

router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=ClientRead,
    status_code=status.HTTP_201_CREATED,
)
def creer_nouveau_client(
    donnees: ClientCreate,
    db: Session = Depends(get_db),
):
    try:
        return creer_client(db, donnees)
    except TelephoneDejaUtiliseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce numéro de téléphone est déjà utilisé.",
        )


@router.get(
    "/{client_id}",
    response_model=ClientRead,
)
def consulter_client(
    client_id: int,
    db: Session = Depends(get_db),
):
    client = obtenir_client_par_id(db, client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable.",
        )

    return client

@router.get(
    "",
    response_model=ClientListResponse,
)
def lister_tous_les_clients(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    clients, total = lister_clients(db, limit, offset)

    return {
        "items": clients,
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@router.patch(
    "/{client_id}",
    response_model=ClientRead,
)
def modifier_un_client(
    client_id: int,
    donnees: ClientUpdate,
    db: Session = Depends(get_db),
):
    try:
        client = modifier_client(db, client_id, donnees)
    except TelephoneDejaUtiliseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce numéro de téléphone est déjà utilisé.",
        )

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable.",
        )

    return client