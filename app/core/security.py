from pwdlib import PasswordHash


# utilise l'algorithme Argon2 (recommandé pour le hachage des mots de passe)
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Transforme un mot de passe en hash sécurisé."""
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe correspond à son hash."""
    return password_hasher.verify(password, hashed_password)