from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTypeEnum(str, Enum):
    """Tipos de dispositivo permitidos."""

    laptop = "laptop"
    tablet = "tablet"
    proyector = "proyector"
    camara = "camara"
    router = "router"
    monitor = "monitor"


# Esquema base con los campos comunes
class DeviceBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Nombre descriptivo del dispositivo")
    serial_number: str = Field(..., min_length=3, max_length=100, description="Número de serie único del dispositivo")
    device_type: DeviceTypeEnum = Field(..., description="Tipo de dispositivo")
    brand: Optional[str] = Field(None, max_length=50, description="Marca del dispositivo (opcional)")
    is_available: bool = Field(True, description="Indica si el dispositivo está disponible para préstamo")


# Esquema para crear (POST) y reemplazar completamente (PUT)
class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(DeviceBase):
    pass


# Esquema para actualizar parcialmente (PATCH) - todos los campos opcionales
class DevicePatch(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    serial_number: Optional[str] = Field(None, min_length=3, max_length=100)
    device_type: Optional[DeviceTypeEnum] = None
    brand: Optional[str] = Field(None, max_length=50)
    is_available: Optional[bool] = None


# Esquema para responder al cliente
class DeviceResponse(DeviceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Versión reducida del dispositivo, usada dentro de LoanDetailResponse
class DeviceBasicInfo(BaseModel):
    id: int
    name: str
    serial_number: str
    device_type: DeviceTypeEnum

    class Config:
        from_attributes = True
