from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.utilisateur import Utilisateur


def exiger_roles(*roles_autorises: str):
    """Vérifie que l'utilisateur possède un rôle autorisé."""

    def verifier_role(
        utilisateur: Utilisateur = Depends(get_current_user),
    ) -> Utilisateur:
        if utilisateur.role not in roles_autorises:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les permissions nécessaires.",
            )

        return utilisateur

    return verifier_role