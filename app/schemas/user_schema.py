from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.validators import validate_strong_password


class RoleEnum(str, Enum):
    """Roles permitidos para un usuario dentro de device_systems."""

    admin = "admin"
    support = "support"
    user = "user"


# Esquema base con los campos comunes (sin contraseña, no se expone en respuestas)
class UserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Nombre completo, mínimo 3 caracteres")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    role: RoleEnum = Field(..., description="Rol del usuario: admin, support o user")
    is_active: bool = Field(True, description="Estado activo o inactivo del usuario")


# Esquema para crear (POST) un usuario directamente (uso administrativo).
# Requiere contraseña, igual que el auto-registro en /auth/register.
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Contraseña segura (mín. 8 car., mayúscula, minúscula y número)")

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return validate_strong_password(value)


# Esquema para reemplazar completamente (PUT). La contraseña es opcional:
# si se envía, se actualiza; si no, se conserva la actual.
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8, description="Nueva contraseña (opcional)")

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_strong_password(value)


# Esquema para actualizar parcialmente (PATCH) - Todos los campos son opcionales
class UserPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return validate_strong_password(value)


# Esquema para responder al cliente (incluye el ID generado y la fecha de
# creación). NUNCA incluye hashed_password ni password.
class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
