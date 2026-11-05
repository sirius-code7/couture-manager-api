from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base commune de tous les modèles SQLAlchemy."""

    pass


# importer les modèles pour les enregistrer dans Base.metadata.
from app.models.utilisateur import Utilisateur  # noqa: E402, F401