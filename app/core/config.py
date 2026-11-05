
from pydantic_settings import BaseSettings, SettingsConfigDict

# core.py centralise les paramètres généraux de l'app

class Settings(BaseSettings):
    # paramètres généraux de l'api
    app_name: str = "Couture Manager API"
    app_description: str = "API de gestion d'un atelier de couture."
    app_version: str = "1.0.0"
    environment: str = "development"
        # paramètres de sécurité JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # adresse de connexion à postgreSQL
    database_url: str

    # charge les variables depuis le fichier .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# instance unique des paramètres
settings = Settings()
