from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Réponse renvoyée après une authentification réussie."""

    access_token: str
    token_type: str = "bearer"