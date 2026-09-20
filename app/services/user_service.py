"""
Capa de servicios de usuarios.

Concentra toda la lógica de acceso a datos (consultas, creación,
actualización, eliminación, filtros y orden) para mantener las rutas
(`user_routes.py`) enfocadas únicamente en manejar la petición HTTP.
"""

from typing import Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.auth.security import get_password_hash
from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserPatch, UserUpdate

# Campos válidos para ordenar resultados
ORDERABLE_FIELDS = {
    "name": User.name,
    "-name": User.name,
    "created_at": User.created_at,
    "-created_at": User.created_at,
}


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca un usuario por su correo electrónico."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Busca un usuario por su ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_users(
    db: Session,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    order_by: Optional[str] = None,
) -> list[User]:
    """Lista usuarios aplicando filtros opcionales de rol, estado y orden."""
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if order_by in ORDERABLE_FIELDS:
        column = ORDERABLE_FIELDS[order_by]
        query = query.order_by(desc(column) if order_by.startswith("-") else asc(column))

    return query.all()


def create_user(db: Session, user: UserCreate, role_override: Optional[str] = None) -> User:
    """
    Crea y persiste un nuevo usuario en la base de datos, hasheando su
    contraseña antes de guardarla (nunca se almacena en texto plano).

    `role_override` permite forzar un rol (por ejemplo, "user" para el
    auto-registro público en /auth/register), ignorando el que venga en
    el payload si se necesita.
    """
    user_data = user.model_dump(exclude={"password"})
    if role_override is not None:
        user_data["role"] = role_override

    new_user = User(**user_data, hashed_password=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(db: Session, db_user: User, user: UserUpdate) -> User:
    """Reemplaza por completo los datos de un usuario existente."""
    update_data = user.model_dump(exclude={"password"})
    for field, value in update_data.items():
        setattr(db_user, field, value)

    if user.password:
        db_user.hashed_password = get_password_hash(user.password)

    db.commit()
    db.refresh(db_user)
    return db_user


def patch_user(db: Session, db_user: User, user: UserPatch) -> User:
    """Actualiza parcialmente un usuario, solo con los campos enviados."""
    update_data = user.model_dump(exclude_unset=True, exclude={"password"})
    for field, value in update_data.items():
        setattr(db_user, field, value)

    if user.password:
        db_user.hashed_password = get_password_hash(user.password)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, db_user: User) -> None:
    """Elimina un usuario de la base de datos."""
    db.delete(db_user)
    db.commit()
