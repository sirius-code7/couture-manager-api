from pydantic import BaseModel, ConfigDict, Field


class TypeVetementCreate(BaseModel):
    """Données nécessaires pour créer une prestation."""

    nom: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    prix_base: int = Field(
        gt=0,
        description="Prix de base en FCFA.",
    )

    delai_jours: int = Field(
        ge=0,
        description="Délai de réalisation en jours.",
    )


class TypeVetementUpdate(BaseModel):
    """Données modifiables d'une prestation."""

    nom: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    prix_base: int | None = Field(
        default=None,
        gt=0,
    )

    delai_jours: int | None = Field(
        default=None,
        ge=0,
    )

    actif: bool | None = None


class TypeVetementRead(BaseModel):
    """Données publiques d'une prestation."""

    id: int
    nom: str
    description: str | None
    prix_base: int
    delai_jours: int
    actif: bool

    model_config = ConfigDict(from_attributes=True)