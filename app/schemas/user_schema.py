from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RoleEnum(str, Enum):
    """Roles permitidos para un usuario dentro de device_systems."""

    admin = "admin"
    support = "support"
    user = "user"


# Esquema base con los campos comunes
class UserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Nombre completo, mínimo 3 caracteres")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    role: RoleEnum = Field(..., description="Rol del usuario: admin, support o user")
    is_active: bool = Field(True, description="Estado activo o inactivo del usuario")


# Esquema para crear (POST) y reemplazar completamente (PUT)
class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


# Esquema para actualizar parcialmente (PATCH) - Todos los campos son opcionales
class UserPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


# Esquema para responder al cliente (incluye el ID generado y la fecha de creación)
class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
