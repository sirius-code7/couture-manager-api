from sqlalchemy import text

from fastapi import FastAPI

from app.core.config import settings
from app.database.session import engine

from app.routers.auth import router as auth_router

from app.routers import client

from app.routers import mesure

from app.routers import utilisateur

from app.routers import type_vetement

from app.routers import commande

from app.routers import paiement

from app.routers import livraison

from app.routers import statistique

# initialise l'API avec les paramètres centralisés
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(utilisateur.router, prefix="/api/v1")
app.include_router(client.router, prefix="/api/v1")
app.include_router(mesure.router, prefix="/api/v1")
app.include_router(type_vetement.router, prefix="/api/v1")
app.include_router(commande.router, prefix="/api/v1")
app.include_router(paiement.router, prefix="/api/v1")
app.include_router(livraison.router, prefix="/api/v1")
app.include_router(statistique.router)

@app.get("/health")
def verifier_etat_api():
    """Vérifie que l'API et PostgreSQL sont accessibles."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"status": "ok"}