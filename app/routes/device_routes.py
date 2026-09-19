from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import require_admin, require_admin_or_support
from app.dependencies.database_dependency import get_db
from app.schemas.device_schema import (
    DeviceCreate,
    DevicePatch,
    DeviceResponse,
    DeviceTypeEnum,
    DeviceUpdate,
)
from app.schemas.loan_schema import LoanDetailResponse
from app.services import device_service, loan_service

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo dispositivo",
    response_description="Dispositivo creado correctamente",
    dependencies=[Depends(require_admin_or_support)],
)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Crea un dispositivo, validando que el número de serie no esté duplicado."""
    if device_service.get_device_by_serial(db, device.serial_number):
        raise HTTPException(status_code=400, detail="El número de serie ya está registrado.")
    return device_service.create_device(db, device)


@router.get(
    "/",
    response_model=List[DeviceResponse],
    summary="Listar dispositivos",
    response_description="Lista de dispositivos, con filtros opcionales",
)
def get_devices(
    device_type: Optional[DeviceTypeEnum] = Query(None, description="Filtra por tipo de dispositivo"),
    is_available: Optional[bool] = Query(None, description="Filtra por disponibilidad"),
    brand: Optional[str] = Query(None, description="Filtra por marca (coincidencia parcial)"),
    search: Optional[str] = Query(None, description="Búsqueda parcial por nombre, número de serie o marca"),
    db: Session = Depends(get_db),
):
    """Lista dispositivos, permitiendo combinar filtros por tipo, disponibilidad, marca o búsqueda libre."""
    return device_service.get_devices(
        db,
        device_type=device_type.value if device_type else None,
        is_available=is_available,
        brand=brand,
        search=search,
    )


@router.get(
    "/{device_id}/loans",
    response_model=List[LoanDetailResponse],
    summary="Consultar el historial de préstamos de un dispositivo",
)
def get_device_loans(device_id: int, db: Session = Depends(get_db)):
    """Retorna el historial de préstamos (activos e históricos) de un dispositivo, con datos del usuario."""
    db_device = device_service.get_device_by_id(db, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")

    loans = loan_service.get_loans(db, device_id=device_id)
    return [loan_service.to_loan_detail(loan) for loan in loans]


@router.get("/{device_id}", response_model=DeviceResponse, summary="Consultar un dispositivo por ID")
def get_device(device_id: int, db: Session = Depends(get_db)):
    db_device = device_service.get_device_by_id(db, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")
    return db_device


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Reemplazar un dispositivo completo",
    dependencies=[Depends(require_admin_or_support)],
)
def update_device(device_id: int, device: DeviceUpdate, db: Session = Depends(get_db)):
    db_device = device_service.get_device_by_id(db, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")

    other_device = device_service.get_device_by_serial(db, device.serial_number)
    if other_device and other_device.id != device_id:
        raise HTTPException(status_code=400, detail="El número de serie ya está registrado por otro dispositivo.")

    return device_service.update_device(db, db_device, device)


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Actualizar un dispositivo parcialmente",
    dependencies=[Depends(require_admin_or_support)],
)
def patch_device(device_id: int, device: DevicePatch, db: Session = Depends(get_db)):
    db_device = device_service.get_device_by_id(db, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")

    update_data = device.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="El cuerpo de la petición no puede estar vacío.")

    if "serial_number" in update_data:
        other_device = device_service.get_device_by_serial(db, update_data["serial_number"])
        if other_device and other_device.id != device_id:
            raise HTTPException(status_code=400, detail="El número de serie ya está registrado por otro dispositivo.")

    return device_service.patch_device(db, db_device, device)


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un dispositivo",
    dependencies=[Depends(require_admin)],
)
def delete_device(device_id: int, db: Session = Depends(get_db)):
    db_device = device_service.get_device_by_id(db, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")
    device_service.delete_device(db, db_device)
    return None
