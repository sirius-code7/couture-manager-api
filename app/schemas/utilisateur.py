from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleUtilisateur(StrEnum):
    """Rôles autorisés dans l'application."""

    ADMIN = "admin"
    TAILLEUR = "tailleur"
    ACCUEIL = "accueil"


class UtilisateurCreate(BaseModel):
    """Données nécessaires pour créer un utilisateur."""

    email: EmailStr
    nom_complet: str = Field(min_length=1, max_length=255)
    mot_de_passe: str = Field(min_length=8)
    role: RoleUtilisateur = RoleUtilisateur.ACCUEIL


class UtilisateurUpdate(BaseModel):
    """Données modifiables d'un utilisateur."""

    nom_complet: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    mot_de_passe: str | None = Field(
        default=None,
        min_length=8,
    )
    role: RoleUtilisateur | None = None
    actif: bool | None = None


class UtilisateurRead(BaseModel):
    """Données publiques d'un utilisateur."""

    id: int
    email: EmailStr
    nom_complet: str
    role: RoleUtilisateur
    actif: bool
    created_at: datetime

    # permet de lire un modèle SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

class UtilisateurListResponse(BaseModel):
    """Résultat paginé de la liste des utilisateurs."""

    items: list[UtilisateurRead]
    total: int
    limit: int
    offset: int