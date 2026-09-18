from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.device_schema import DeviceBasicInfo


class LoanStatusEnum(str, Enum):
    """Estados posibles de un préstamo."""

    active = "active"
    returned = "returned"
    overdue = "overdue"


# Esquema para crear un préstamo (POST /loans)
class LoanCreate(BaseModel):
    user_id: int = Field(..., description="ID del usuario que solicita el préstamo")
    device_id: int = Field(..., description="ID del dispositivo a prestar")


# Esquema para actualizar el estado de un préstamo
class LoanUpdate(BaseModel):
    status: LoanStatusEnum = Field(..., description="Nuevo estado del préstamo")
    return_date: Optional[datetime] = Field(None, description="Fecha de devolución (si aplica)")


# Versión reducida del usuario, usada dentro de LoanDetailResponse
class UserBasicInfo(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


# Esquema de respuesta simple (sin datos relacionados expandidos)
class LoanResponse(BaseModel):
    id: int
    user_id: int
    device_id: int
    loan_date: datetime
    return_date: Optional[datetime] = None
    status: LoanStatusEnum

    class Config:
        from_attributes = True


# Esquema de respuesta con información relacionada de usuario y dispositivo
class LoanDetailResponse(BaseModel):
    loan_id: int
    status: LoanStatusEnum
    loan_date: datetime
    return_date: Optional[datetime] = None
    user: UserBasicInfo
    device: DeviceBasicInfo

    class Config:
        from_attributes = True
