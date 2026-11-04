
from fastapi import FastAPI

from app.core.config import settings


# initialise l'api avec les paramètres centralisés
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)


@app.get("/health")
def verifier_etat_api():
    """Vérifie que l'API est opérationnelle."""
    return {"status": "ok"}
