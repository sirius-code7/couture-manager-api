from datetime import date, timedelta
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.mesure import Mesure
from app.models.type_vetement import TypeVetement
from app.models.commande import Commande, LigneCommande, HistoriqueStatut
from app.schemas.commande import (
    ChangementStatutCreate,
    CommandeCreate,
    CommandeUpdate,
    LigneCommandeCreate,
)


class CommandeIntrouvableError(Exception):
    pass


class ClientCommandeIntrouvableError(Exception):
    pass


class MesureCommandeInvalideError(Exception):
    pass


class PrestationCommandeInvalideError(Exception):
    pass


class CommandeInvalideError(Exception):
    pass


class LigneCommandeIntrouvableError(Exception):
    pass

class DonneesCommandeInvalidesError(Exception):
    pass

TRANSITIONS_STATUT = {
    "en_attente": {"en_coupe", "annulee"},
    "en_coupe": {"en_couture", "annulee"},
    "en_couture": {"essayage", "terminee", "annulee"},
    "essayage": {"retouches", "terminee", "annulee"},
    "retouches": {"essayage", "terminee", "annulee"},
    "terminee": set(),
    "livree": set(),
    "annulee": set(),
}


def _obtenir_commande(db: Session, commande_id: int) -> Commande:
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise CommandeIntrouvableError

    return commande


def _obtenir_lignes(db: Session, commande_id: int) -> list[LigneCommande]:
    requete = (
        select(LigneCommande)
        .where(LigneCommande.commande_id == commande_id)
        .order_by(LigneCommande.id)
    )
    return list(db.scalars(requete).all())


def _construire_reponse(db: Session, commande: Commande) -> dict:
    lignes = _obtenir_lignes(db, commande.id)

    return {
        "id": commande.id,
        "numero": commande.numero,
        "client_id": commande.client_id,
        "mesure_id": commande.mesure_id,
        "statut": commande.statut,
        "date_commande": commande.date_commande,
        "date_livraison_prevue": commande.date_livraison_prevue,
        "date_livraison_reelle": commande.date_livraison_reelle,
        "remise": commande.remise,
        "montant_total": commande.montant_total,
        "montant_paye": commande.montant_paye,
        "montant_restant": commande.montant_total - commande.montant_paye,
        "en_retard": (
            commande.date_livraison_prevue < date.today()
            and commande.statut not in {"livree", "annulee"}
        ),
        "notes": commande.notes,
        "cree_par_id": commande.cree_par_id,
        "created_at": commande.created_at,
        "updated_at": commande.updated_at,
        "lignes": lignes,
    }


def _calculer_montant(
    db: Session,
    commande: Commande,
    remise: int | None = None,
) -> int:
    lignes = _obtenir_lignes(db, commande.id)
    sous_total = sum(
        ligne.quantite * ligne.prix_unitaire
        for ligne in lignes
    )
    remise_finale = commande.remise if remise is None else remise

    if remise_finale > sous_total:
        raise CommandeInvalideError(
            "La remise ne peut pas dépasser le montant des prestations."
        )

    montant_total = sous_total - remise_finale

    if montant_total < commande.montant_paye:
        raise CommandeInvalideError(
            "Le montant total ne peut pas être inférieur au montant déjà payé."
        )

    return montant_total


def _generer_numero(db: Session, date_commande: date) -> str:
    prefixe = f"CMD-{date_commande.year}-"

    dernier_numero = db.scalar(
        select(Commande.numero)
        .where(Commande.numero.like(f"{prefixe}%"))
        .order_by(desc(Commande.numero))
        .limit(1)
    )

    sequence = int(dernier_numero.split("-")[-1]) + 1 if dernier_numero else 1

    return f"{prefixe}{sequence:05d}"


def _preparer_ligne(
    db: Session,
    donnees: LigneCommandeCreate,
) -> LigneCommande:
    prestation = db.get(TypeVetement, donnees.type_vetement_id)

    if prestation is None or not prestation.actif:
        raise PrestationCommandeInvalideError(
            "La prestation est introuvable ou inactive."
        )

    return LigneCommande(
        type_vetement_id=prestation.id,
        description=donnees.description,
        quantite=donnees.quantite,
        prix_unitaire=(
            donnees.prix_unitaire
            if donnees.prix_unitaire is not None
            else prestation.prix_base
        ),
    )


def creer_commande(
    db: Session,
    utilisateur_id: int,
    donnees: CommandeCreate,
) -> dict:
    client = db.get(Client, donnees.client_id)

    if client is None:
        raise ClientCommandeIntrouvableError

    mesure_id = donnees.mesure_id

    if mesure_id is not None:
        mesure = db.get(Mesure, mesure_id)

        if mesure is None or mesure.client_id != donnees.client_id:
            raise MesureCommandeInvalideError(
                "La mesure sélectionnée n'appartient pas à ce client."
            )
    else:
        derniere_mesure = db.scalar(
            select(Mesure)
            .where(Mesure.client_id == donnees.client_id)
            .order_by(desc(Mesure.date_prise), desc(Mesure.id))
            .limit(1)
        )
        mesure_id = derniere_mesure.id if derniere_mesure else None

    lignes_preparees = [
        _preparer_ligne(db, ligne)
        for ligne in donnees.lignes
    ]

    delai_max = max(
        db.get(TypeVetement, ligne.type_vetement_id).delai_jours
        for ligne in donnees.lignes
    )

    date_livraison = donnees.date_livraison_prevue or (
    donnees.date_commande + timedelta(days=delai_max)
)

    if date_livraison < donnees.date_commande:
        raise CommandeInvalideError(
            "La date de livraison ne peut pas précéder la date de commande."
        )

    sous_total = sum(
        ligne.quantite * ligne.prix_unitaire
        for ligne in lignes_preparees
    )

    if donnees.remise > sous_total:
        raise CommandeInvalideError(
            "La remise ne peut pas dépasser le montant des prestations."
        )

    commande = Commande(
        numero=_generer_numero(db, donnees.date_commande),
        client_id=donnees.client_id,
        mesure_id=mesure_id,
        statut="en_attente",
        date_commande=donnees.date_commande,
        date_livraison_prevue=date_livraison,
        remise=donnees.remise,
        montant_total=sous_total - donnees.remise,
        montant_paye=0,
        notes=donnees.notes,
        cree_par_id=utilisateur_id,
    )

    try:
        db.add(commande)
        db.flush()

        for ligne in lignes_preparees:
            ligne.commande_id = commande.id
            db.add(ligne)

        db.add(
            HistoriqueStatut(
                commande_id=commande.id,
                ancien_statut=None,
                nouveau_statut="en_attente",
                commentaire="Création de la commande.",
                modifie_par_id=utilisateur_id,
            )
        )

        db.commit()
        db.refresh(commande)

        return _construire_reponse(db, commande)

    except Exception:
        db.rollback()
        raise


def lister_commandes(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    statut: str | None = None,
    client_id: int | None = None,
) -> tuple[list[dict], int]:
    requete = select(Commande)

    if statut is not None:
        requete = requete.where(Commande.statut == statut)

    if client_id is not None:
        requete = requete.where(Commande.client_id == client_id)

    total = db.scalar(
        select(func.count()).select_from(requete.subquery())
    ) or 0

    commandes = db.scalars(
        requete
        .order_by(desc(Commande.date_commande), desc(Commande.id))
        .limit(limit)
        .offset(offset)
    ).all()

    return [
        _construire_reponse(db, commande)
        for commande in commandes
    ], total


def consulter_commande(db: Session, commande_id: int) -> dict:
    commande = _obtenir_commande(db, commande_id)
    return _construire_reponse(db, commande)


def modifier_commande(
    db: Session,
    commande_id: int,
    donnees: CommandeUpdate,
) -> dict:
    commande = _obtenir_commande(db, commande_id)

    if commande.statut != "en_attente":
        raise CommandeInvalideError(
            "Seules les commandes en attente peuvent être modifiées."
        )

    modifications = donnees.model_dump(exclude_unset=True)

    if "remise" in modifications and modifications["remise"] is None:
        raise DonneesCommandeInvalidesError(
            "La remise ne peut pas être vide."
    )

    if (
        "date_livraison_prevue" in modifications
        and modifications["date_livraison_prevue"] is None
    ):
        raise CommandeInvalideError(
            "La date de livraison prévue ne peut pas être vide."
        )

    date_livraison = modifications.get(
        "date_livraison_prevue",
        commande.date_livraison_prevue,
    )

    if date_livraison < commande.date_commande:
        raise CommandeInvalideError(
            "La date de livraison ne peut pas précéder la date de commande."
        )

    remise = modifications.get("remise", commande.remise)
    montant_total = _calculer_montant(db, commande, remise)

    try:
        for champ, valeur in modifications.items():
            setattr(commande, champ, valeur)

        commande.montant_total = montant_total

        db.commit()
        db.refresh(commande)

        return _construire_reponse(db, commande)

    except Exception:
        db.rollback()
        raise


def ajouter_ligne_commande(
    db: Session,
    commande_id: int,
    donnees: LigneCommandeCreate,
) -> dict:
    commande = _obtenir_commande(db, commande_id)

    if commande.statut != "en_attente":
        raise CommandeInvalideError(
            "Les lignes ne peuvent être modifiées que lorsque la commande est en attente."
        )

    ligne = _preparer_ligne(db, donnees)

    try:
        ligne.commande_id = commande.id
        db.add(ligne)
        db.flush()

        commande.montant_total = _calculer_montant(db, commande)

        db.commit()
        db.refresh(commande)

        return _construire_reponse(db, commande)

    except Exception:
        db.rollback()
        raise


def supprimer_ligne_commande(
    db: Session,
    ligne_id: int,
) -> dict:
    ligne = db.get(LigneCommande, ligne_id)

    if ligne is None:
        raise LigneCommandeIntrouvableError

    commande = _obtenir_commande(db, ligne.commande_id)

    if commande.statut != "en_attente":
        raise CommandeInvalideError(
            "Les lignes ne peuvent être modifiées que lorsque la commande est en attente."
        )

    lignes = _obtenir_lignes(db, commande.id)

    if len(lignes) <= 1:
        raise CommandeInvalideError(
            "Une commande doit conserver au moins une ligne."
        )

    try:
        db.delete(ligne)
        db.flush()

        commande.montant_total = _calculer_montant(db, commande)

        db.commit()
        db.refresh(commande)

        return _construire_reponse(db, commande)

    except Exception:
        db.rollback()
        raise


def changer_statut_commande(
    db: Session,
    commande_id: int,
    utilisateur_id: int,
    donnees: ChangementStatutCreate,
) -> dict:
    commande = _obtenir_commande(db, commande_id)
    nouveau_statut = donnees.statut

    if nouveau_statut == commande.statut:
        raise CommandeInvalideError(
            "La commande possède déjà ce statut."
        )

    if nouveau_statut == "livree":
        raise CommandeInvalideError(
            "La livraison doit être confirmée depuis la fonctionnalité Livraisons."
        )

    transitions = TRANSITIONS_STATUT.get(commande.statut, set())

    if nouveau_statut not in transitions:
        raise CommandeInvalideError(
            f"Transition impossible : {commande.statut} vers {nouveau_statut}."
        )

    if nouveau_statut == "annulee" and commande.montant_paye > 0:
        commentaire = (donnees.commentaire or "").lower()
        mots_remboursement = (
            "rembours",
            "restitu",
            "rendu",
            "remise au client",
        )

        if not any(mot in commentaire for mot in mots_remboursement):
            raise DonneesCommandeInvalidesError(
                "Le commentaire doit préciser le remboursement ou la restitution de l'acompte."
        )

    ancien_statut = commande.statut

    try:
        commande.statut = nouveau_statut

        db.add(
            HistoriqueStatut(
                commande_id=commande.id,
                ancien_statut=ancien_statut,
                nouveau_statut=nouveau_statut,
                commentaire=donnees.commentaire,
                modifie_par_id=utilisateur_id,
            )
        )

        db.commit()
        db.refresh(commande)

        return _construire_reponse(db, commande)

    except Exception:
        db.rollback()
        raise


def lister_historique_commande(
    db: Session,
    commande_id: int,
) -> list[HistoriqueStatut]:
    _obtenir_commande(db, commande_id)

    requete = (
        select(HistoriqueStatut)
        .where(HistoriqueStatut.commande_id == commande_id)
        .order_by(HistoriqueStatut.date_modification, HistoriqueStatut.id)
    )

    return list(db.scalars(requete).all())