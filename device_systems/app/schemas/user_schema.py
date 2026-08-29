"""
Esquemas Pydantic para el recurso 'usuarios' de device_systems.

Se definen tres tipos de modelos:
- UserBase: campos compartidos.
- UserCreate: modelo de entrada para el registro (POST /users).
- UserResponse: modelo de salida (response_model), evita exponer
  campos que no queremos devolver al cliente.
"""

from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRole(str, Enum):
    """Roles permitidos para un usuario del sistema."""
    admin = "admin"
    support = "support"
    user = "user"


class UserBase(BaseModel):
    """Campos base compartidos entre entrada y salida."""
    name: str = Field(
        ...,
        min_length=3,
        description="Nombre completo del usuario, mínimo 3 caracteres.",
        examples=["Juan Mejía"],
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico válido y único del usuario.",
        examples=["juan.mejia@example.com"],
    )
    role: UserRole = Field(
        default=UserRole.user,
        description="Rol del usuario: admin, support o user.",
    )
    is_active: bool = Field(
        default=True,
        description="Indica si el usuario está activo en el sistema.",
    )


class UserCreate(UserBase):
    """Modelo de entrada usado en POST /users."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Juan Mejía",
                "email": "juan.mejia@example.com",
                "role": "admin",
                "is_active": True,
            }
        }
    )


class UserResponse(UserBase):
    """Modelo de salida (response_model) para exponer un usuario."""
    id: int = Field(..., description="Identificador único del usuario.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Juan Mejía",
                "email": "juan.mejia@example.com",
                "role": "admin",
                "is_active": True,
            }
        },
    )
