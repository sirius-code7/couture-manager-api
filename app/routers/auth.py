from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.token import creer_access_token
from app.database.session import get_db
from app.schemas.auth import TokenResponse
from app.services.utilisateur import authentifier_utilisateur

from app.dependencies.auth import get_current_user
from app.schemas.utilisateur import UtilisateurRead

from app.models.utilisateur import Utilisateur


router = APIRouter(
    prefix="/auth",
    tags=["Authentification"],
)


@router.post("/login", response_model=TokenResponse)
def login(
    formulaire: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authentifie un utilisateur et génère un jeton JWT."""

    utilisateur = authentifier_utilisateur(
        db=db,
        email=formulaire.username,
        mot_de_passe=formulaire.password,
    )

    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = creer_access_token(
        utilisateur_id=utilisateur.id,
        role=utilisateur.role,
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UtilisateurRead)
def lire_utilisateur_connecte(
    utilisateur: Utilisateur = Depends(get_current_user),
):
    """Retourne les informations de l'utilisateur connecté."""

    return utilisateur