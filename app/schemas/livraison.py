from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


MODES_LIVRAISON = (
    "retrait_atelier",
    "domicile",
)

STATUTS_LIVRAISON = (
    "planifiee",
    "livree",
)


class LivraisonPlanifier(BaseModel):
    mode: str
    adresse: str | None = Field(default=None, max_length=1000)
    livreur: str | None = Field(default=None, max_length=150)
    date_prevue: date
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("mode")
    @classmethod
    def valider_mode(cls, valeur: str) -> str:
        if valeur not in MODES_LIVRAISON:
            raise ValueError("Mode de livraison invalide.")
        return valeur

    @field_validator("adresse", "livreur", "notes")
    @classmethod
    def nettoyer_texte(cls, valeur: str | None) -> str | None:
        if valeur is None:
            return None

        valeur = valeur.strip()
        return valeur or None

    @model_validator(mode="after")
    def verifier_adresse_domicile(self):
        if self.mode == "domicile" and not self.adresse:
            raise ValueError(
                "L'adresse est obligatoire pour une livraison à domicile."
            )

        return self


class LivraisonConfirmer(BaseModel):
    autoriser_solde_impaye: bool = False
    date_effective: date = Field(default_factory=date.today)
    commentaire: str | None = Field(default=None, max_length=2000)

    @field_validator("commentaire")
    @classmethod
    def nettoyer_commentaire(cls, valeur: str | None) -> str | None:
        if valeur is None:
            return None

        valeur = valeur.strip()
        return valeur or None


class LivraisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    mode: str
    adresse: str | None
    livreur: str | None
    date_prevue: date
    date_effective: date | None
    statut: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class LivraisonTourneeRead(BaseModel):
    livraison_id: int
    commande_id: int
    numero_commande: str
    client_nom: str
    client_prenom: str
    client_telephone: str
    mode: str
    adresse: str | None
    livreur: str | None
    date_prevue: date
    date_effective: date | None
    statut: str
    montant_restant: int