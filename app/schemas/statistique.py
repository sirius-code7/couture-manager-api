from datetime import date

from pydantic import BaseModel, ConfigDict


class TableauBordRead(BaseModel):
    chiffre_affaires_mois: int
    encaisse_mois: int
    nb_commandes_mois: int
    reste_a_encaisser: int
    commandes_par_statut: dict[str, int]
    nb_commandes_en_retard: int
    commandes_pretes_a_livrer: int
    livraisons_du_jour: int


class ChiffreAffairesItem(BaseModel):
    periode: date
    chiffre_affaires: int
    encaisse: int


class ChiffreAffairesRead(BaseModel):
    granularite: str
    date_debut: date
    date_fin: date
    items: list[ChiffreAffairesItem]


class TypeVetementStatistiqueRead(BaseModel):
    type_vetement_id: int
    nom: str
    quantite: int
    chiffre_affaires: int


class TopClientRead(BaseModel):
    client_id: int
    nom: str
    prenom: str
    telephone: str
    nb_commandes: int
    chiffre_affaires: int
    solde_du: int


class ImpayeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    client_nom: str
    client_telephone: str
    statut: str
    date_livraison_prevue: date
    montant_total: int
    montant_paye: int
    solde: int


class ImpayesRead(BaseModel):
    items: list[ImpayeItemRead]
    total: int
    limit: int
    offset: int