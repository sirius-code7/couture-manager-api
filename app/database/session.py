from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# moteur de connexion à PostgreSQL
engine = create_engine(settings.database_url)

# fabrique de sessions pour communiquer avec la base
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    """Fournit une session de base de données par requête."""
    db: Session = SessionLocal()

    try:
        yield db
    finally:
        db.close()