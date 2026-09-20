"""
Modelo SQLAlchemy para la tabla `users` de device_systems.

Este modelo representa la estructura real de la tabla en la base de datos
y es independiente de los schemas Pydantic utilizados para validar
la entrada y salida de datos en la API.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class User(Base):
    """Representa un registro de usuario almacenado en la base de datos."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    # Nunca se expone en los schemas de respuesta (UserResponse no la incluye)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Un usuario puede tener muchos préstamos
    loans = relationship("Loan", back_populates="user")
