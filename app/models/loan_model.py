"""
Modelo SQLAlchemy para la tabla `loans` de device_systems.

Representa el préstamo de un dispositivo (`Device`) a un usuario (`User`),
manteniendo la trazabilidad de fechas y el estado del préstamo.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Loan(Base):
    """Representa el préstamo de un dispositivo a un usuario."""

    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    loan_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    return_date = Column(DateTime, nullable=True)
    # Estados: active, returned, overdue
    status = Column(String, nullable=False, default="active")

    # Cada préstamo pertenece a un único usuario y a un único dispositivo
    user = relationship("User", back_populates="loans")
    device = relationship("Device", back_populates="loans")
