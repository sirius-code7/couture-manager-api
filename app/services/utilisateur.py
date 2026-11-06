from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurUpdate


class EmailDejaUtiliseError(Exception):
    """Signale qu'une adresse e-mail est déjà utilisée."""


class ModificationUtilisateurInvalideError(Exception):
    """Signale une modification interdite ou invalide."""


def creer_utilisateur(
    db: Session,
    donnees: UtilisateurCreate,
) -> Utilisateur:
    """Crée un utilisateur en enregistrant uniquement le hash du mot de passe."""

    # vérifie si l'adresse e-mail existe déjà
    utilisateur_existant = db.scalar(
        select(Utilisateur).where(Utilisateur.email == donnees.email)
    )

    if utilisateur_existant:
        raise EmailDejaUtiliseError(
            "Cette adresse e-mail est déjà utilisée."
        )

    utilisateur = Utilisateur(
        email=donnees.email,
        nom_complet=donnees.nom_complet,
        mot_de_passe_hash=hash_password(donnees.mot_de_passe),
        role=donnees.role.value,
    )

    db.add(utilisateur)

    try:
        db.commit()
        db.refresh(utilisateur)
    except IntegrityError as erreur:

        # protège aussi contre deux créations simultanées du même e-mail
        db.rollback()
        raise EmailDejaUtiliseError(
            "Cette adresse e-mail est déjà utilisée."
        ) from erreur

    return utilisateur


def authentifier_utilisateur(
    db: Session,
    email: str,
    mot_de_passe: str,
) -> Utilisateur | None:
    """Vérifie les identifiants d'un utilisateur."""

    utilisateur = db.scalar(
        select(Utilisateur).where(Utilisateur.email == email)
    )

    if utilisateur is None or not utilisateur.actif:
        return None

    if not verify_password(
        mot_de_passe,
        utilisateur.mot_de_passe_hash,
    ):
        return None

    return utilisateur


def lister_utilisateurs(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Utilisateur], int]:
    """Retourne les utilisateurs avec pagination."""

    utilisateurs = db.scalars(
        select(Utilisateur)
        .order_by(Utilisateur.id)
        .limit(limit)
        .offset(offset)
    ).all()

    total = db.scalar(
        select(func.count()).select_from(Utilisateur)
    )

    return list(utilisateurs), total or 0


def obtenir_utilisateur_par_id(
    db: Session,
    utilisateur_id: int,
) -> Utilisateur | None:
    """Recherche un utilisateur par son identifiant."""

    return db.get(Utilisateur, utilisateur_id)


def modifier_utilisateur(
    db: Session,
    utilisateur_id: int,
    donnees: UtilisateurUpdate,
    utilisateur_connecte: Utilisateur,
) -> Utilisateur | None:
    """Modifie un utilisateur en appliquant les règles de sécurité."""

    utilisateur = obtenir_utilisateur_par_id(db, utilisateur_id)

    if utilisateur is None:
        return None

    modifications = donnees.model_dump(exclude_unset=True)

    if not modifications:
        raise ModificationUtilisateurInvalideError(
            "Aucune modification n'a été fournie."
        )

    if any(valeur is None for valeur in modifications.values()):
        raise ModificationUtilisateurInvalideError(
            "Les champs modifiés ne peuvent pas être nuls."
        )

    # RG24 : un administrateur ne peut pas se désactiver lui-même
    if (
        utilisateur.id == utilisateur_connecte.id
        and modifications.get("actif") is False
    ):
        raise ModificationUtilisateurInvalideError(
            "Un administrateur ne peut pas désactiver son propre compte."
        )

    # RG24 : un administrateur ne peut pas retirer son propre rôle admin
    nouveau_role = modifications.get("role")

    if (
        utilisateur.id == utilisateur_connecte.id
        and nouveau_role is not None
        and nouveau_role.value != "admin"
    ):
        raise ModificationUtilisateurInvalideError(
            "Un administrateur ne peut pas retirer son propre rôle admin."
        )

    if "mot_de_passe" in modifications:
        utilisateur.mot_de_passe_hash = hash_password(
            modifications.pop("mot_de_passe")
        )

    if "role" in modifications:
        utilisateur.role = modifications.pop("role").value

    for champ, valeur in modifications.items():
        setattr(utilisateur, champ, valeur)

    try:
        db.commit()
        db.refresh(utilisateur)
    except IntegrityError:
        db.rollback()
        raise

    return utilisateur