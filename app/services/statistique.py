from datetime import date

from sqlalchemy import Date, func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.commande import (
    Commande,
    LigneCommande,
    STATUTS_COMMANDE,
)
from app.models.livraison import Livraison
from app.models.paiement import Paiement
from app.models.type_vetement import TypeVetement


STATUTS_FINAUX = ("livree", "annulee")


def obtenir_tableau_de_bord(db: Session) -> dict:
    aujourd_hui = date.today()
    debut_mois = aujourd_hui.replace(day=1)

    chiffre_affaires = db.scalar(
        select(func.coalesce(func.sum(Commande.montant_total), 0)).where(
            Commande.date_commande >= debut_mois,
            Commande.date_commande <= aujourd_hui,
            Commande.statut != "annulee",
        )
    )

    encaisse = db.scalar(
        select(func.coalesce(func.sum(Paiement.montant), 0)).where(
            Paiement.date_paiement >= debut_mois,
            Paiement.date_paiement <= aujourd_hui,
        )
    )

    nb_commandes = db.scalar(
        select(func.count(Commande.id)).where(
            Commande.date_commande >= debut_mois,
            Commande.date_commande <= aujourd_hui,
            Commande.statut != "annulee",
        )
    )

    reste_a_encaisser = db.scalar(
        select(
            func.coalesce(
                func.sum(Commande.montant_total - Commande.montant_paye),
                0,
            )
        ).where(Commande.statut != "annulee")
    )

    resultats_statuts = db.execute(
        select(Commande.statut, func.count(Commande.id))
        .group_by(Commande.statut)
    ).all()

    commandes_par_statut = {
        statut: 0 for statut in STATUTS_COMMANDE
    }

    for statut, nombre in resultats_statuts:
        commandes_par_statut[statut] = nombre

    nb_en_retard = db.scalar(
        select(func.count(Commande.id)).where(
            Commande.date_livraison_prevue < aujourd_hui,
            Commande.statut.not_in(STATUTS_FINAUX),
        )
    )

    pretes_a_livrer = db.scalar(
        select(func.count(Commande.id)).where(
            Commande.statut == "terminee"
        )
    )

    livraisons_du_jour = db.scalar(
    select(func.count(Livraison.id)).where(
        Livraison.date_prevue == aujourd_hui,
    )
)

    return {
        "chiffre_affaires_mois": int(chiffre_affaires or 0),
        "encaisse_mois": int(encaisse or 0),
        "nb_commandes_mois": int(nb_commandes or 0),
        "reste_a_encaisser": int(reste_a_encaisser or 0),
        "commandes_par_statut": commandes_par_statut,
        "nb_commandes_en_retard": int(nb_en_retard or 0),
        "commandes_pretes_a_livrer": int(pretes_a_livrer or 0),
        "livraisons_du_jour": int(livraisons_du_jour or 0),
    }


def obtenir_chiffre_affaires(
    db: Session,
    granularite: str,
    date_debut: date,
    date_fin: date,
) -> dict:
    if date_debut > date_fin:
        raise ValueError("La date de début doit précéder la date de fin.")

    if granularite not in ("jour", "mois"):
        raise ValueError("La granularité doit être 'jour' ou 'mois'.")

    unite = "day" if granularite == "jour" else "month"

    periode_commandes = func.date_trunc(
        unite,
        Commande.date_commande,
    ).cast(Date)

    resultats_ca = db.execute(
        select(
            periode_commandes.label("periode"),
            func.sum(Commande.montant_total).label("montant"),
        )
        .where(
            Commande.date_commande >= date_debut,
            Commande.date_commande <= date_fin,
            Commande.statut != "annulee",
        )
        .group_by(periode_commandes)
    ).all()

    periode_paiements = func.date_trunc(
        unite,
        Paiement.date_paiement,
    ).cast(Date)

    resultats_encaissements = db.execute(
        select(
            periode_paiements.label("periode"),
            func.sum(Paiement.montant).label("montant"),
        )
        .where(
            Paiement.date_paiement >= date_debut,
            Paiement.date_paiement <= date_fin,
        )
        .group_by(periode_paiements)
    ).all()

    totaux = {}

    for periode, montant in resultats_ca:
        totaux[periode] = {
            "chiffre_affaires": int(montant or 0),
            "encaisse": 0,
        }

    for periode, montant in resultats_encaissements:
        if periode not in totaux:
            totaux[periode] = {
                "chiffre_affaires": 0,
                "encaisse": 0,
            }

        totaux[periode]["encaisse"] = int(montant or 0)

    items = [
        {
            "periode": periode,
            **montants,
        }
        for periode, montants in sorted(totaux.items())
    ]

    return {
        "granularite": granularite,
        "date_debut": date_debut,
        "date_fin": date_fin,
        "items": items,
    }


def obtenir_statistiques_types_vetement(
    db: Session,
    date_debut: date,
    date_fin: date,
) -> list[dict]:
    if date_debut > date_fin:
        raise ValueError("La date de début doit précéder la date de fin.")

    resultats = db.execute(
        select(
            TypeVetement.id,
            TypeVetement.nom,
            func.sum(LigneCommande.quantite).label("quantite"),
            func.sum(
                LigneCommande.quantite * LigneCommande.prix_unitaire
            ).label("chiffre_affaires"),
        )
        .join(
            LigneCommande,
            LigneCommande.type_vetement_id == TypeVetement.id,
        )
        .join(
            Commande,
            Commande.id == LigneCommande.commande_id,
        )
        .where(
            Commande.date_commande >= date_debut,
            Commande.date_commande <= date_fin,
            Commande.statut != "annulee",
        )
        .group_by(TypeVetement.id, TypeVetement.nom)
        .order_by(func.sum(
            LigneCommande.quantite * LigneCommande.prix_unitaire
        ).desc())
    ).all()

    return [
        {
            "type_vetement_id": identifiant,
            "nom": nom,
            "quantite": int(quantite or 0),
            "chiffre_affaires": int(chiffre_affaires or 0),
        }
        for identifiant, nom, quantite, chiffre_affaires in resultats
    ]


def obtenir_top_clients(
    db: Session,
    date_debut: date,
    date_fin: date,
    limite: int,
) -> list[dict]:
    if date_debut > date_fin:
        raise ValueError("La date de début doit précéder la date de fin.")

    resultats = db.execute(
        select(
            Client.id,
            Client.nom,
            Client.prenom,
            Client.telephone,
            func.count(Commande.id).label("nb_commandes"),
            func.sum(Commande.montant_total).label("chiffre_affaires"),
            func.sum(
                Commande.montant_total - Commande.montant_paye
            ).label("solde_du"),
        )
        .join(Commande, Commande.client_id == Client.id)
        .where(
            Commande.date_commande >= date_debut,
            Commande.date_commande <= date_fin,
            Commande.statut != "annulee",
        )
        .group_by(
            Client.id,
            Client.nom,
            Client.prenom,
            Client.telephone,
        )
        .order_by(func.sum(Commande.montant_total).desc())
        .limit(limite)
    ).all()

    return [
        {
            "client_id": identifiant,
            "nom": nom,
            "prenom": prenom,
            "telephone": telephone,
            "nb_commandes": int(nb_commandes or 0),
            "chiffre_affaires": int(chiffre_affaires or 0),
            "solde_du": int(solde_du or 0),
        }
        for (
            identifiant,
            nom,
            prenom,
            telephone,
            nb_commandes,
            chiffre_affaires,
            solde_du,
        ) in resultats
    ]


def obtenir_impayes(
    db: Session,
    limit: int,
    offset: int,
) -> dict:
    filtres = (
        Commande.statut != "annulee",
        Commande.montant_total > Commande.montant_paye,
    )

    total = db.scalar(
        select(func.count(Commande.id)).where(*filtres)
    )

    resultats = db.execute(
        select(
            Commande.id,
            Commande.numero,
            Client.nom,
            Client.prenom,
            Client.telephone,
            Commande.statut,
            Commande.date_livraison_prevue,
            Commande.montant_total,
            Commande.montant_paye,
        )
        .join(Client, Client.id == Commande.client_id)
        .where(*filtres)
        .order_by(
            Commande.date_livraison_prevue.asc(),
            Commande.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()

    items = [
        {
            "id": identifiant,
            "numero": numero,
            "client_nom": f"{prenom} {nom}",
            "client_telephone": telephone,
            "statut": statut,
            "date_livraison_prevue": date_prevue,
            "montant_total": montant_total,
            "montant_paye": montant_paye,
            "solde": montant_total - montant_paye,
        }
        for (
            identifiant,
            numero,
            nom,
            prenom,
            telephone,
            statut,
            date_prevue,
            montant_total,
            montant_paye,
        ) in resultats
    ]

    return {
        "items": items,
        "total": int(total or 0),
        "limit": limit,
        "offset": offset,
    }