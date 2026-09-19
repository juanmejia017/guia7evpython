"""
Lógica de negocio de autenticación: verificación de credenciales y emisión
de tokens JWT. Mantiene `auth_routes.py` enfocado en la petición HTTP.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.auth.security import create_access_token, verify_password
from app.models.user_model import User
from app.services import user_service


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Verifica las credenciales de un usuario.
    Retorna el usuario si son válidas, o None si el correo no existe o la
    contraseña es incorrecta.
    """
    db_user = user_service.get_user_by_email(db, email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def generate_token_for_user(user: User) -> str:
    """Genera un token JWT para un usuario autenticado, usando su email como `sub`."""
    return create_access_token(data={"sub": user.email, "role": user.role})
