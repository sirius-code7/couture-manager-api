
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.commande import Commande


MODES_PAIEMENT = (
    "especes",
    "wave",
    "orange_money",
    "virement",
    "cheque",
)

MODE_PAIEMENT_ENUM = Enum(
    *MODES_PAIEMENT,
    name="mode_paiement",
)


class Paiement(Base):
    __tablename__ = "paiements"

    id: Mapped[int] = mapped_column(primary_key=True)

    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    montant: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    mode: Mapped[str] = mapped_column(
        MODE_PAIEMENT_ENUM,
        nullable=False,
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    date_paiement: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    enregistre_par_id: Mapped[int] = mapped_column(
        ForeignKey("utilisateurs.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    commande: Mapped["Commande"] = relationship(
        back_populates="paiements",
    )

    enregistre_par: Mapped["Utilisateur"] = relationship( # type: ignore
        "Utilisateur",
        foreign_keys=[enregistre_par_id],
    )
