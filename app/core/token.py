from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def creer_access_token(
    utilisateur_id: int,
    role: str,
) -> str:
    """Génère un jeton JWT pour un utilisateur."""

    maintenant = datetime.now(timezone.utc)

    expiration = maintenant + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    # informations intégrées au jeton
    payload = {
        "sub": str(utilisateur_id),
        "role": role,
        "iat": maintenant,
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verifier_access_token(token: str) -> dict:
    """Vérifie la signature et l'expiration d'un jeton JWT."""

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )