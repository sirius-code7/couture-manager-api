from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.commande import Commande
from app.models.paiement import Paiement
from app.schemas.paiement import PaiementCreate


class CommandePaiementIntrouvableError(Exception):
    pass


class PaiementIntrouvableError(Exception):
    pass


class PaiementImpossibleError(Exception):
    pass


def enregistrer_paiement(
    db: Session,
    commande_id: int,
    utilisateur_id: int,
    donnees: PaiementCreate,
) -> Paiement:
    try:
        commande = db.scalar(
            select(Commande)
            .where(Commande.id == commande_id)
            .with_for_update()
        )

        if commande is None:
            raise CommandePaiementIntrouvableError(
                "Commande introuvable."
            )

        if commande.statut == "annulee":
            raise PaiementImpossibleError(
                "Impossible d'enregistrer un paiement sur une commande annulée."
            )

        montant_restant = commande.montant_total - commande.montant_paye

        if donnees.montant > montant_restant:
            raise PaiementImpossibleError(
                f"Le montant dépasse le solde restant de {montant_restant} FCFA."
            )

        paiement = Paiement(
            commande_id=commande_id,
            montant=donnees.montant,
            mode=donnees.mode,
            reference=donnees.reference,
            date_paiement=donnees.date_paiement,
            enregistre_par_id=utilisateur_id,
        )

        db.add(paiement)
        commande.montant_paye += donnees.montant

        db.commit()
        db.refresh(paiement)

        return paiement

    except Exception:
        db.rollback()
        raise


def lister_paiements_commande(
    db: Session,
    commande_id: int,
) -> list[Paiement]:
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise CommandePaiementIntrouvableError(
            "Commande introuvable."
        )

    requete = (
        select(Paiement)
        .where(Paiement.commande_id == commande_id)
        .order_by(Paiement.date_paiement.desc(), Paiement.id.desc())
    )

    return list(db.scalars(requete).all())


def supprimer_paiement(
    db: Session,
    paiement_id: int,
) -> None:
    try:
        paiement = db.get(Paiement, paiement_id)

        if paiement is None:
            raise PaiementIntrouvableError(
                "Paiement introuvable."
            )

        commande = db.scalar(
            select(Commande)
            .where(Commande.id == paiement.commande_id)
            .with_for_update()
        )

        if commande is None:
            raise CommandePaiementIntrouvableError(
                "Commande associée au paiement introuvable."
            )

        paiement = db.scalar(
            select(Paiement)
            .where(Paiement.id == paiement_id)
            .with_for_update()
        )

        if paiement is None:
            raise PaiementIntrouvableError(
                "Paiement introuvable."
            )

        db.delete(paiement)
        db.flush()

        montant_paye = db.scalar(
            select(func.coalesce(func.sum(Paiement.montant), 0))
            .where(Paiement.commande_id == commande.id)
        )

        commande.montant_paye = int(montant_paye or 0)

        db.commit()

    except Exception:
        db.rollback()
        raise