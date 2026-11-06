from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator


STATUTS_AUTORISES = (
    "en_attente",
    "en_coupe",
    "en_couture",
    "essayage",
    "retouches",
    "terminee",
    "livree",
    "annulee",
)

class LigneCommandeCreate(BaseModel):
    type_vetement_id: int = Field(gt=0)
    description: str | None = None
    quantite: int = Field(gt=0)
    prix_unitaire: int | None = Field(default=None, gt=0)


class CommandeCreate(BaseModel):
    client_id: int = Field(gt=0)
    mesure_id: int | None = Field(default=None, gt=0)
    date_commande: date = Field(default_factory=date.today)
    date_livraison_prevue: date | None = None
    remise: int = Field(default=0, ge=0)
    notes: str | None = None
    lignes: list[LigneCommandeCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def verifier_dates(self):
        if self.date_commande > date.today():
            raise ValueError("La date de commande ne peut pas être dans le futur.")

        if (
            self.date_livraison_prevue is not None
            and self.date_livraison_prevue < self.date_commande
        ):
            raise ValueError(
                "La date de livraison ne peut pas précéder la date de commande."
            )

        return self


class CommandeUpdate(BaseModel):
    date_livraison_prevue: date | None = None
    remise: int | None = Field(default=None, ge=0)
    notes: str | None = None


class ChangementStatutCreate(BaseModel):
    statut: str
    commentaire: str | None = None

    @model_validator(mode="after")
    def verifier_statut(self):
        if self.statut not in STATUTS_AUTORISES:
            raise ValueError("Le statut indiqué est invalide.")
        return self


class LigneCommandeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    type_vetement_id: int
    description: str | None
    quantite: int
    prix_unitaire: int


class HistoriqueStatutRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    ancien_statut: str | None
    nouveau_statut: str
    commentaire: str | None
    modifie_par_id: int
    date_modification: datetime


class CommandeRead(BaseModel):
    id: int
    numero: str
    client_id: int
    mesure_id: int | None
    statut: str
    date_commande: date
    date_livraison_prevue: date
    date_livraison_reelle: date | None
    remise: int
    montant_total: int
    montant_paye: int
    montant_restant: int
    en_retard: bool
    notes: str | None
    cree_par_id: int
    created_at: datetime
    updated_at: datetime
    lignes: list[LigneCommandeRead]


class CommandeListResponse(BaseModel):
    items: list[CommandeRead]
    total: int
    limit: int
    offset: int