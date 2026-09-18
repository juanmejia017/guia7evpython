"""
Modelo SQLAlchemy para la tabla `devices` de device_systems.

Representa los equipos tecnológicos (laptops, tablets, proyectores, etc.)
disponibles para ser prestados a los usuarios.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Device(Base):
    """Representa un dispositivo tecnológico disponible para préstamo."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    serial_number = Column(String, unique=True, nullable=False, index=True)
    device_type = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Un dispositivo puede aparecer en muchos préstamos históricos
    loans = relationship("Loan", back_populates="device")
