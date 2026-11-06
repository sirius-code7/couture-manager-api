from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TypeVetement(Base):
    """Représente une prestation disponible dans le catalogue."""

    __tablename__ = "types_vetement"

    id: Mapped[int] = mapped_column(primary_key=True)

    nom: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    prix_base: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    delai_jours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # une prestation inactive reste conservée pour l'historique
    actif: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )