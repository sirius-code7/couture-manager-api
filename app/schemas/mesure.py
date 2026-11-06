from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CHAMPS_MESURES = (
    "taille_cm",
    "tour_cou",
    "carrure_dos",
    "longueur_epaule",
    "tour_poitrine",
    "tour_taille",
    "tour_bassin",
    "longueur_manche",
    "tour_bras",
    "tour_poignet",
    "longueur_dos",
    "longueur_haut",
    "longueur_pantalon",
    "tour_cuisse",
    "tour_genou",
    "bas_pantalon",
    "entrejambe",
    "longueur_robe",
)


class MesureBase(BaseModel):
    date_prise: date | None = None
    notes: str | None = None

    taille_cm: Decimal | None = Field(default=None, gt=0, le=300)
    tour_cou: Decimal | None = Field(default=None, gt=0, le=300)
    carrure_dos: Decimal | None = Field(default=None, gt=0, le=300)
    longueur_epaule: Decimal | None = Field(default=None, gt=0, le=300)
    tour_poitrine: Decimal | None = Field(default=None, gt=0, le=300)
    tour_taille: Decimal | None = Field(default=None, gt=0, le=300)
    tour_bassin: Decimal | None = Field(default=None, gt=0, le=300)
    longueur_manche: Decimal | None = Field(default=None, gt=0, le=300)
    tour_bras: Decimal | None = Field(default=None, gt=0, le=300)
    tour_poignet: Decimal | None = Field(default=None, gt=0, le=300)
    longueur_dos: Decimal | None = Field(default=None, gt=0, le=300)
    longueur_haut: Decimal | None = Field(default=None, gt=0, le=300)
    longueur_pantalon: Decimal | None = Field(default=None, gt=0, le=300)
    tour_cuisse: Decimal | None = Field(default=None, gt=0, le=300)
    tour_genou: Decimal | None = Field(default=None, gt=0, le=300)
    bas_pantalon: Decimal | None = Field(default=None, gt=0, le=300)
    entrejambe: Decimal | None = Field(default=None, gt=0, le=300)
    longueur_robe: Decimal | None = Field(default=None, gt=0, le=300)

    @field_validator("date_prise")
    @classmethod
    def verifier_date_prise(cls, valeur):
        if valeur is not None and valeur > date.today():
            raise ValueError("La date de prise ne peut pas être dans le futur.")
        return valeur


class MesureCreate(MesureBase):
    date_prise: date = Field(default_factory=date.today)

    @model_validator(mode="after")
    def verifier_presence_mesure(self):
        if not any(getattr(self, champ) is not None for champ in CHAMPS_MESURES):
            raise ValueError("Au moins une mesure doit être renseignée.")
        return self


class MesureUpdate(MesureBase):
    pass


class MesureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    date_prise: date
    prise_par_id: int
    notes: str | None

    taille_cm: Decimal | None
    tour_cou: Decimal | None
    carrure_dos: Decimal | None
    longueur_epaule: Decimal | None
    tour_poitrine: Decimal | None
    tour_taille: Decimal | None
    tour_bassin: Decimal | None
    longueur_manche: Decimal | None
    tour_bras: Decimal | None
    tour_poignet: Decimal | None
    longueur_dos: Decimal | None
    longueur_haut: Decimal | None
    longueur_pantalon: Decimal | None
    tour_cuisse: Decimal | None
    tour_genou: Decimal | None
    bas_pantalon: Decimal | None
    entrejambe: Decimal | None
    longueur_robe: Decimal | None