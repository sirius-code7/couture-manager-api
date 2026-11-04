from sqlalchemy import text

from fastapi import FastAPI

from app.core.config import settings
from app.database.session import engine

# Initialise l'API avec les paramètres centralisés
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)


@app.get("/health")
def verifier_etat_api():
    """Vérifie que l'API et PostgreSQL sont accessibles."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"status": "ok"}