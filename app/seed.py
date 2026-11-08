
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models import TypeVetement, Utilisateur


PRESTATIONS = [
    {
        "nom": "Boubou",
        "description": "Boubou homme en bazin ou brodé",
        "prix_base": 35000,
        "delai_jours": 10,
    },
    {
        "nom": "Costume 2 pièces",
        "description": "Veste et pantalon",
        "prix_base": 85000,
        "delai_jours": 14,
    },
    {
        "nom": "Robe",
        "description": "Robe sur mesure",
        "prix_base": 30000,
        "delai_jours": 7,
    },
    {
        "nom": "Ensemble wax",
        "description": "Tenue deux pièces en wax",
        "prix_base": 25000,
        "delai_jours": 7,
    },
    {
        "nom": "Chemise",
        "description": "Chemise sur mesure",
        "prix_base": 15000,
        "delai_jours": 5,
    },
    {
        "nom": "Pantalon",
        "description": "Pantalon sur mesure",
        "prix_base": 12000,
        "delai_jours": 4,
    },
    {
        "nom": "Retouche",
        "description": "Ourlet, rétrécissement, remplacement de fermeture",
        "prix_base": 3000,
        "delai_jours": 2,
    },
]


def initialiser_catalogue(db):
    ajouts = 0

    for donnees in PRESTATIONS:
        prestation = db.scalar(
            select(TypeVetement).where(
                TypeVetement.nom == donnees["nom"]
            )
        )

        if prestation is None:
            db.add(TypeVetement(**donnees, actif=True))
            ajouts += 1

    print(f"Catalogue : {ajouts} prestation(s) ajoutée(s).")


def initialiser_administrateur(db):
    administrateur = db.scalar(
        select(Utilisateur).where(
            Utilisateur.role == "admin"
        )
    )

    if administrateur is not None:
        print(
            f"Administrateur existant conservé : "
            f"{administrateur.email}"
        )
        return

    email = os.getenv("ADMIN_EMAIL")
    nom_complet = os.getenv("ADMIN_NOM_COMPLET")
    mot_de_passe = os.getenv("ADMIN_PASSWORD")

    if not all([email, nom_complet, mot_de_passe]):
        raise ValueError(
            "Aucun administrateur trouvé. "
            "Définissez ADMIN_EMAIL, ADMIN_NOM_COMPLET "
            "et ADMIN_PASSWORD."
        )

    administrateur = Utilisateur(
        email=email.strip().lower(),
        nom_complet=nom_complet.strip(),
        mot_de_passe_hash=hash_password(mot_de_passe),
        role="admin",
        actif=True,
    )

    db.add(administrateur)
    print(f"Administrateur initial créé : {email}")


def main():
    db = SessionLocal()

    try:
        initialiser_catalogue(db)
        initialiser_administrateur(db)

        db.commit()
        print("Initialisation terminée avec succès.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
