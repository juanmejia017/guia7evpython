"""
Capa de servicios de préstamos (loans).

Contiene la lógica de negocio del préstamo de dispositivos: creación,
devolución, y consultas con joins/filtros que combinan información de
usuarios, dispositivos y préstamos.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.device_model import Device
from app.models.loan_model import Loan
from app.models.user_model import User
from app.schemas.loan_schema import LoanCreate


def get_loan_by_id(db: Session, loan_id: int) -> Optional[Loan]:
    """Busca un préstamo por su ID, precargando usuario y dispositivo."""
    return (
        db.query(Loan)
        .options(joinedload(Loan.user), joinedload(Loan.device))
        .filter(Loan.id == loan_id)
        .first()
    )


def get_loans(
    db: Session,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    device_id: Optional[int] = None,
    user_email: Optional[str] = None,
    device_type: Optional[str] = None,
) -> list[Loan]:
    """
    Lista préstamos combinando información de users y devices mediante join(),
    aplicando filtros opcionales con where()/and_() e ilike() para búsquedas
    parciales de correo.
    """
    query = (
        db.query(Loan)
        .join(User, Loan.user_id == User.id)
        .join(Device, Loan.device_id == Device.id)
        .options(joinedload(Loan.user), joinedload(Loan.device))
    )

    filters = []
    if status:
        filters.append(Loan.status == status)
    if user_id is not None:
        filters.append(Loan.user_id == user_id)
    if device_id is not None:
        filters.append(Loan.device_id == device_id)
    if user_email:
        filters.append(User.email.ilike(f"%{user_email}%"))
    if device_type:
        filters.append(Device.device_type == device_type)

    if filters:
        query = query.where(and_(*filters))

    return query.all()


def create_loan(db: Session, loan: LoanCreate, device: Device) -> Loan:
    """Crea un préstamo y marca el dispositivo como no disponible."""
    new_loan = Loan(user_id=loan.user_id, device_id=loan.device_id, status="active")
    device.is_available = False
    db.add(new_loan)
    db.add(device)
    db.commit()
    db.refresh(new_loan)
    return new_loan


def return_loan(db: Session, db_loan: Loan) -> Loan:
    """Marca un préstamo como devuelto y libera el dispositivo asociado."""
    db_loan.status = "returned"
    db_loan.return_date = datetime.utcnow()
    if db_loan.device is not None:
        db_loan.device.is_available = True
    db.commit()
    db.refresh(db_loan)
    return db_loan


def to_loan_detail(loan: Loan) -> dict:
    """Convierte un Loan (con user y device ya cargados) al formato de LoanDetailResponse."""
    return {
        "loan_id": loan.id,
        "status": loan.status,
        "loan_date": loan.loan_date,
        "return_date": loan.return_date,
        "user": {
            "id": loan.user.id,
            "name": loan.user.name,
            "email": loan.user.email,
        },
        "device": {
            "id": loan.device.id,
            "name": loan.device.name,
            "serial_number": loan.device.serial_number,
            "device_type": loan.device.device_type,
        },
    }
