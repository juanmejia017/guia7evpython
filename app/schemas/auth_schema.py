from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user_schema import RoleEnum
from app.schemas.validators import validate_strong_password


class UserRegister(BaseModel):
    """Datos requeridos para el auto-registro de un usuario (`POST /auth/register`)."""

    name: str = Field(..., min_length=3, max_length=50, description="Nombre completo, mínimo 3 caracteres")
    email: EmailStr = Field(..., description="Correo electrónico válido y único")
    password: str = Field(..., min_length=8, description="Contraseña segura (mín. 8 car., mayúscula, minúscula y número)")
    role: RoleEnum = Field(RoleEnum.user, description="Rol del usuario: admin, support o user")

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return validate_strong_password(value)


class UserLogin(BaseModel):
    """Credenciales para iniciar sesión (`POST /auth/login`)."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Respuesta del login: token de acceso JWT."""

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    """Datos extraídos del payload de un token JWT decodificado."""

    email: Optional[str] = None
