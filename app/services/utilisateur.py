from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate


class EmailDejaUtiliseError(Exception):
    """Signale qu'une adresse e-mail est déjà utilisée."""


def creer_utilisateur(
    db: Session,
    donnees: UtilisateurCreate,
) -> Utilisateur:
    """Crée un utilisateur en enregistrant uniquement le hash du mot de passe."""

    # vérifie si l'adresse e-mail existe déjà
    utilisateur_existant = db.scalar(
        select(Utilisateur).where(Utilisateur.email == donnees.email)
    )

    if utilisateur_existant:
        raise EmailDejaUtiliseError("Cette adresse e-mail est déjà utilisée.")

    utilisateur = Utilisateur(
        email=donnees.email,
        nom_complet=donnees.nom_complet,
        mot_de_passe_hash=hash_password(donnees.mot_de_passe),
        role=donnees.role.value,
    )

    db.add(utilisateur)

    try:
        db.commit()
        db.refresh(utilisateur)
    except IntegrityError as erreur:
        # protège aussi contre deux créations simultanées du même e-mail
        db.rollback()
        raise EmailDejaUtiliseError(
            "Cette adresse e-mail est déjà utilisée."
        ) from erreur

    return utilisateur