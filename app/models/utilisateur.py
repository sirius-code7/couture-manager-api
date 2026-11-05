from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Utilisateur(Base):
    """Représente un utilisateur de l'atelier."""

    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    nom_complet: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # seul le hash est stocké, jamais le mot de passe en clair.
    mot_de_passe_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        Enum(
            "admin",
            "tailleur",
            "accueil",
            name="role_utilisateur",
        ),
        nullable=False,
        default="accueil",
    )

    actif: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )