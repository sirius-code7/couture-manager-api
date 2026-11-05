from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.utilisateur import Utilisateur


def authentifier_utilisateur(
    db: Session,
    email: str,
    mot_de_passe: str,
) -> Utilisateur | None:
    """Vérifie les identifiants et retourne l'utilisateur authentifié."""

    utilisateur = db.scalar(
        select(Utilisateur).where(Utilisateur.email == email)
    )

    if utilisateur is None:
        return None

    if not verify_password(
        mot_de_passe,
        utilisateur.mot_de_passe_hash,
    ):
        return None

    if not utilisateur.actif:
        return None

    return utilisateur