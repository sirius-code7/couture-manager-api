
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ModePaiement = Literal[
    "especes",
    "wave",
    "orange_money",
    "virement",
    "cheque",
]


class PaiementCreate(BaseModel):
    montant: int = Field(gt=0)
    mode: ModePaiement
    reference: str | None = Field(default=None, max_length=100)
    date_paiement: date = Field(default_factory=date.today)

    @field_validator("reference")
    @classmethod
    def nettoyer_reference(cls, valeur: str | None) -> str | None:
        if valeur is None:
            return None

        valeur = valeur.strip()
        return valeur or None

    @model_validator(mode="after")
    def verifier_date_paiement(self):
        if self.date_paiement > date.today():
            raise ValueError(
                "La date du paiement ne peut pas être dans le futur."
            )

        return self


class PaiementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    montant: int
    mode: str
    reference: str | None
    date_paiement: date
    enregistre_par_id: int
    created_at: datetime
