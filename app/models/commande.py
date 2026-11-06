from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


STATUTS_COMMANDE = (
    "en_attente",
    "en_coupe",
    "en_couture",
    "essayage",
    "retouches",
    "terminee",
    "livree",
    "annulee",
)

STATUT_COMMANDE_ENUM = Enum(
    *STATUTS_COMMANDE,
    name="statut_commande",
)


class Commande(Base):
    __tablename__ = "commandes"

    id: Mapped[int] = mapped_column(primary_key=True)

    numero: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    mesure_id: Mapped[int | None] = mapped_column(
        ForeignKey("mesures.id", ondelete="RESTRICT"),
        nullable=True,
)

    statut: Mapped[str] = mapped_column(
        STATUT_COMMANDE_ENUM,
        nullable=False,
        default="en_attente",
    )

    date_commande: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    date_livraison_prevue: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    date_livraison_reelle: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    remise: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    montant_total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    montant_paye: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cree_par_id: Mapped[int] = mapped_column(
        ForeignKey("utilisateurs.id"),
        nullable=False,
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


class LigneCommande(Base):
    __tablename__ = "lignes_commande"

    id: Mapped[int] = mapped_column(primary_key=True)

    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type_vetement_id: Mapped[int] = mapped_column(
        ForeignKey("types_vetement.id", ondelete="RESTRICT"),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    quantite: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    prix_unitaire: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


class HistoriqueStatut(Base):
    __tablename__ = "historique_statuts"

    id: Mapped[int] = mapped_column(primary_key=True)

    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ancien_statut: Mapped[str | None] = mapped_column(
        STATUT_COMMANDE_ENUM,
        nullable=True,
    )

    nouveau_statut: Mapped[str] = mapped_column(
        STATUT_COMMANDE_ENUM,
        nullable=False,
    )

    commentaire: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    modifie_par_id: Mapped[int] = mapped_column(
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_modification: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )