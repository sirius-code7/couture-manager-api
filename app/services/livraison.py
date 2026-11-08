from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.client import Client
from app.models.commande import Commande, HistoriqueStatut
from app.models.livraison import Livraison
from app.schemas.livraison import (
    LivraisonConfirmer,
    LivraisonPlanifier,
)


class CommandeLivraisonIntrouvableError(Exception):
    pass


class LivraisonIntrouvableError(Exception):
    pass


class LivraisonImpossibleError(Exception):
    pass


def planifier_livraison(
    db: Session,
    commande_id: int,
    donnees: LivraisonPlanifier,
) -> Livraison:
    try:
        commande = db.scalar(
            select(Commande)
            .where(Commande.id == commande_id)
            .with_for_update()
        )

        if commande is None:
            raise CommandeLivraisonIntrouvableError(
                "Commande introuvable."
            )

        if commande.statut in {"livree", "annulee"}:
            raise LivraisonImpossibleError(
                "Impossible de planifier une livraison pour cette commande."
            )

        livraison = db.scalar(
            select(Livraison)
            .where(Livraison.commande_id == commande_id)
            .with_for_update()
        )

        if livraison is None:
            livraison = Livraison(
                commande_id=commande_id,
                mode=donnees.mode,
                adresse=donnees.adresse,
                livreur=donnees.livreur,
                date_prevue=donnees.date_prevue,
                notes=donnees.notes,
            )
            db.add(livraison)
        else:
            if livraison.statut == "livree":
                raise LivraisonImpossibleError(
                    "Cette livraison est déjà confirmée."
                )

            livraison.mode = donnees.mode
            livraison.adresse = donnees.adresse
            livraison.livreur = donnees.livreur
            livraison.date_prevue = donnees.date_prevue
            livraison.notes = donnees.notes

        commande.date_livraison_prevue = donnees.date_prevue

        db.commit()
        db.refresh(livraison)

        return livraison

    except Exception:
        db.rollback()
        raise


def obtenir_livraison(
    db: Session,
    commande_id: int,
) -> Livraison:
    livraison = db.scalar(
        select(Livraison)
        .where(Livraison.commande_id == commande_id)
    )

    if livraison is None:
        commande = db.get(Commande, commande_id)

        if commande is None:
            raise CommandeLivraisonIntrouvableError(
                "Commande introuvable."
            )

        raise LivraisonIntrouvableError(
            "Aucune livraison n'est planifiée pour cette commande."
        )

    return livraison


def confirmer_livraison(
    db: Session,
    commande_id: int,
    utilisateur_id: int,
    donnees: LivraisonConfirmer,
) -> Livraison:
    try:
        commande = db.scalar(
            select(Commande)
            .where(Commande.id == commande_id)
            .with_for_update()
        )

        if commande is None:
            raise CommandeLivraisonIntrouvableError(
                "Commande introuvable."
            )

        if commande.statut != "terminee":
            raise LivraisonImpossibleError(
                "La commande doit être terminée avant sa livraison."
            )

        montant_restant = (
            commande.montant_total - commande.montant_paye
        )

        if montant_restant > 0 and not donnees.autoriser_solde_impaye:
            raise LivraisonImpossibleError(
                "La commande doit être soldée avant la livraison."
            )

        livraison = db.scalar(
            select(Livraison)
            .where(Livraison.commande_id == commande_id)
            .with_for_update()
        )

        if livraison is None:
            livraison = Livraison(
                commande_id=commande_id,
                mode="retrait_atelier",
                adresse=None,
                livreur=None,
                date_prevue=commande.date_livraison_prevue,
                notes=None,
            )
            db.add(livraison)
            db.flush()

        if livraison.statut == "livree":
            raise LivraisonImpossibleError(
                "Cette livraison est déjà confirmée."
            )

        livraison.statut = "livree"
        livraison.date_effective = donnees.date_effective

        commande.statut = "livree"
        commande.date_livraison_reelle = donnees.date_effective

        commentaire = donnees.commentaire

        if montant_restant > 0 and donnees.autoriser_solde_impaye:
            message_solde = (
                f"Livraison confirmée avec un solde impayé "
                f"de {montant_restant} FCFA autorisé."
            )

            if commentaire:
                commentaire = (
                    f"{commentaire} {message_solde}"
                )
            else:
                commentaire = message_solde

        historique = HistoriqueStatut(
            commande_id=commande.id,
            ancien_statut="terminee",
            nouveau_statut="livree",
            commentaire=commentaire,
            modifie_par_id=utilisateur_id,
        )

        db.add(historique)

        db.commit()
        db.refresh(livraison)

        return livraison

    except Exception:
        db.rollback()
        raise


def lister_livraisons(
    db: Session,
    statut: str | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
) -> list[dict]:
    requete = (
        select(Livraison, Commande, Client)
        .join(Commande, Livraison.commande_id == Commande.id)
        .join(Client, Commande.client_id == Client.id)
    )

    if statut is not None:
        requete = requete.where(Livraison.statut == statut)

    if date_min is not None:
        requete = requete.where(
            Livraison.date_prevue >= date_min
        )

    if date_max is not None:
        requete = requete.where(
            Livraison.date_prevue <= date_max
        )

    requete = requete.order_by(
        Livraison.date_prevue.asc(),
        Livraison.id.asc(),
    )

    resultats = db.execute(requete).all()

    return [
        {
            "livraison_id": livraison.id,
            "commande_id": commande.id,
            "numero_commande": commande.numero,
            "client_nom": client.nom,
            "client_prenom": client.prenom,
            "client_telephone": client.telephone,
            "mode": livraison.mode,
            "adresse": livraison.adresse,
            "livreur": livraison.livreur,
            "date_prevue": livraison.date_prevue,
            "date_effective": livraison.date_effective,
            "statut": livraison.statut,
            "montant_restant": (
                commande.montant_total - commande.montant_paye
            ),
        }
        for livraison, commande, client in resultats
    ]