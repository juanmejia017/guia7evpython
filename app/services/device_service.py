"""
Capa de servicios de dispositivos (devices).

Concentra el acceso a datos y las búsquedas/filtros sobre la tabla
`devices`, dejando las rutas enfocadas en la petición HTTP.
"""

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.device_model import Device
from app.schemas.device_schema import DeviceCreate, DevicePatch, DeviceUpdate


def get_device_by_id(db: Session, device_id: int) -> Optional[Device]:
    """Busca un dispositivo por su ID."""
    return db.query(Device).filter(Device.id == device_id).first()


def get_device_by_serial(db: Session, serial_number: str) -> Optional[Device]:
    """Busca un dispositivo por su número de serie."""
    return db.query(Device).filter(Device.serial_number == serial_number).first()


def get_devices(
    db: Session,
    device_type: Optional[str] = None,
    is_available: Optional[bool] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Device]:
    """Lista dispositivos aplicando filtros opcionales de tipo, disponibilidad, marca y búsqueda libre."""
    query = db.query(Device)

    if device_type:
        query = query.filter(Device.device_type == device_type)
    if is_available is not None:
        query = query.filter(Device.is_available == is_available)
    if brand:
        query = query.filter(Device.brand.ilike(f"%{brand}%"))
    if search:
        query = query.filter(
            or_(
                Device.name.ilike(f"%{search}%"),
                Device.serial_number.ilike(f"%{search}%"),
                Device.brand.ilike(f"%{search}%"),
            )
        )

    return query.all()


def create_device(db: Session, device: DeviceCreate) -> Device:
    """Crea y persiste un nuevo dispositivo."""
    new_device = Device(**device.model_dump())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


def update_device(db: Session, db_device: Device, device: DeviceUpdate) -> Device:
    """Reemplaza por completo los datos de un dispositivo existente."""
    for field, value in device.model_dump().items():
        setattr(db_device, field, value)
    db.commit()
    db.refresh(db_device)
    return db_device


def patch_device(db: Session, db_device: Device, device: DevicePatch) -> Device:
    """Actualiza parcialmente un dispositivo, solo con los campos enviados."""
    update_data = device.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_device, field, value)
    db.commit()
    db.refresh(db_device)
    return db_device


def delete_device(db: Session, db_device: Device) -> None:
    """Elimina un dispositivo de la base de datos."""
    db.delete(db_device)
    db.commit()
