
from fastapi import FastAPI

app = FastAPI(
    title="Couture Manager API",
    description="API de gestion d'un atelier de couture.",
    version="1.0.0",
)


@app.get("/health")
def verifier_etat_api():
    """Vérifie que l'API est opérationnelle."""
    return {"status": "ok"}
