"""
Dependencias de autenticación y autorización para proteger rutas.

- `get_current_user`: valida el token JWT del header `Authorization: Bearer <token>`
  y retorna el usuario autenticado. Responde 401 si el token falta, es inválido
  o el usuario ya no existe.
- `get_current_active_user`: además valida que el usuario esté activo.
- `require_roles(*roles)`: fábrica de dependencias que exige que el usuario
  autenticado tenga uno de los roles indicados. Responde 403 si no cumple.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.dependencies.database_dependency import get_db
from app.models.user_model import User
from app.services import user_service

# tokenUrl apunta al endpoint de login; se usa solo para que Swagger UI
# sepa dónde pedir el token (botón "Authorize").
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodifica el token JWT y retorna el usuario autenticado correspondiente."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    db_user = user_service.get_user_by_email(db, email)
    if db_user is None:
        raise credentials_exception

    return db_user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Además de validar el token, exige que el usuario esté activo."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo.")
    return current_user


def require_roles(*allowed_roles: str):
    """
    Fábrica de dependencias: retorna una dependencia que solo deja pasar a
    usuarios autenticados cuyo rol esté dentro de `allowed_roles`.

    Uso: `Depends(require_roles("admin", "support"))`
    """

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción.",
            )
        return current_user

    return role_checker


# Atajos reutilizables para las combinaciones de roles usadas en las rutas
require_admin = require_roles("admin")
require_admin_or_support = require_roles("admin", "support")
