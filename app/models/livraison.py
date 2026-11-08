from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.commande import Commande


class Livraison(Base):
    __tablename__ = "livraisons"

    id: Mapped[int] = mapped_column(primary_key=True)

    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )

    mode: Mapped[str] = mapped_column(
        Enum(
            "retrait_atelier",
            "domicile",
            name="mode_livraison",
        ),
        nullable=False,
    )

    adresse: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    livreur: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    date_prevue: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    date_effective: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str] = mapped_column(
        Enum(
            "planifiee",
            "livree",
            name="statut_livraison",
        ),
        nullable=False,
        default="planifiee",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    commande: Mapped["Commande"] = relationship(
        back_populates="livraison",
    )