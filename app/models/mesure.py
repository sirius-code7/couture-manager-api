from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Mesure(Base):
    __tablename__ = "mesures"

    id: Mapped[int] = mapped_column(primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date_prise: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False,
    )
    prise_par_id: Mapped[int] = mapped_column(
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    taille_cm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    tour_cou: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    carrure_dos: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    longueur_epaule: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    tour_poitrine: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    tour_taille: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    tour_bassin: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    longueur_manche: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    tour_bras: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    tour_poignet: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    longueur_dos: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    longueur_haut: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    longueur_pantalon: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    tour_cuisse: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    tour_genou: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    bas_pantalon: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    entrejambe: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    longueur_robe: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))