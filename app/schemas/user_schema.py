from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Esquema base con los campos comunes
class UserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Nombre completo, mínimo 3 caracteres")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    role: str = Field(..., description="Rol del usuario (ej: admin, user)")
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
    role: Optional[str] = None
    is_active: Optional[bool] = None

# Esquema para responder al cliente (incluye el ID generado)
class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True