from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GenreClient(str, Enum):
    HOMME = "homme"
    FEMME = "femme"
    ENFANT = "enfant"


def normaliser_telephone(valeur: str) -> str:
    """Normalise et valide un numéro de téléphone."""

    telephone = valeur.strip()

    for caractere in (" ", ".", "-", "(", ")"):
        telephone = telephone.replace(caractere, "")

    if telephone.startswith("+"):
        chiffres = telephone[1:]

        if not chiffres.isdigit():
            raise ValueError(
                "Le téléphone doit contenir uniquement des chiffres "
                "avec un + initial facultatif."
            )

        telephone_normalise = f"+{chiffres}"
    else:
        if not telephone.isdigit():
            raise ValueError(
                "Le téléphone doit contenir uniquement des chiffres "
                "avec un + initial facultatif."
            )

        telephone_normalise = telephone

    nombre_chiffres = (
        len(telephone_normalise) - 1
        if telephone_normalise.startswith("+")
        else len(telephone_normalise)
    )

    if not 6 <= nombre_chiffres <= 20:
        raise ValueError(
            "Le téléphone doit contenir entre 6 et 20 chiffres."
        )

    return telephone_normalise


class ClientCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    telephone: str
    email: Optional[str] = Field(default=None, max_length=255)
    adresse: Optional[str] = None
    genre: GenreClient
    notes: Optional[str] = None

    @field_validator("telephone")
    @classmethod
    def valider_telephone(cls, valeur: str) -> str:
        return normaliser_telephone(valeur)


class ClientUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    telephone: Optional[str] = None
    email: Optional[str] = Field(default=None, max_length=255)
    adresse: Optional[str] = None
    genre: Optional[GenreClient] = None
    notes: Optional[str] = None

    @field_validator("telephone")
    @classmethod
    def valider_telephone(
        cls,
        valeur: Optional[str],
    ) -> Optional[str]:
        if valeur is None:
            return valeur

        return normaliser_telephone(valeur)


class ClientRead(BaseModel):
    id: int
    nom: str
    prenom: str
    telephone: str
    email: Optional[str]
    adresse: Optional[str]
    genre: GenreClient
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)