from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import get_current_active_user, require_admin_or_support
from app.dependencies.database_dependency import get_db
from app.rate_limiter import limiter
from app.schemas.device_schema import DeviceTypeEnum
from app.schemas.loan_schema import LoanCreate, LoanDetailResponse, LoanResponse, LoanStatusEnum
from app.services import device_service, loan_service, user_service

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post(
    "/",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un préstamo",
    response_description="Préstamo creado; el dispositivo queda marcado como no disponible",
    dependencies=[Depends(get_current_active_user)],
)
@limiter.limit("10/minute")
def create_loan(request: Request, loan: LoanCreate, db: Session = Depends(get_db)):
    """
    Crea un préstamo validando que:
    - el usuario exista,
    - el dispositivo exista,
    - el dispositivo esté disponible.

    Al crearlo, marca el dispositivo como no disponible (`is_available = False`).
    """
    db_user = user_service.get_user_by_id(db, loan.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    db_device = device_service.get_device_by_id(db, loan.device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")

    if not db_device.is_available:
        raise HTTPException(status_code=409, detail="El dispositivo no está disponible para préstamo.")

    return loan_service.create_loan(db, loan, db_device)


@router.get(
    "/details",
    response_model=List[LoanDetailResponse],
    summary="Listar préstamos con información relacionada (join de usuario y dispositivo)",
    dependencies=[Depends(require_admin_or_support)],
)
def get_loans_details(
    status_: Optional[LoanStatusEnum] = Query(None, alias="status", description="Filtra por estado del préstamo"),
    user_id: Optional[int] = Query(None, description="Filtra por ID de usuario"),
    device_id: Optional[int] = Query(None, description="Filtra por ID de dispositivo"),
    user_email: Optional[str] = Query(None, description="Filtra por correo del usuario (coincidencia parcial)"),
    device_type: Optional[DeviceTypeEnum] = Query(None, description="Filtra por tipo de dispositivo"),
    db: Session = Depends(get_db),
):
    """Lista préstamos mostrando datos básicos del usuario y del dispositivo relacionados."""
    loans = loan_service.get_loans(
        db,
        status=status_.value if status_ else None,
        user_id=user_id,
        device_id=device_id,
        user_email=user_email,
        device_type=device_type.value if device_type else None,
    )
    return [loan_service.to_loan_detail(loan) for loan in loans]


@router.get(
    "/",
    response_model=List[LoanDetailResponse],
    summary="Listar préstamos",
    response_description="Lista de préstamos con filtros opcionales por usuario, dispositivo, estado o correo",
    dependencies=[Depends(require_admin_or_support)],
)
def get_loans(
    status_: Optional[LoanStatusEnum] = Query(None, alias="status", description="Filtra por estado del préstamo"),
    user_id: Optional[int] = Query(None, description="Filtra por ID de usuario"),
    device_id: Optional[int] = Query(None, description="Filtra por ID de dispositivo"),
    user_email: Optional[str] = Query(None, description="Filtra por correo del usuario (coincidencia parcial)"),
    device_type: Optional[DeviceTypeEnum] = Query(None, description="Filtra por tipo de dispositivo"),
    db: Session = Depends(get_db),
):
    return get_loans_details(
        status_=status_,
        user_id=user_id,
        device_id=device_id,
        user_email=user_email,
        device_type=device_type,
        db=db,
    )


@router.get(
    "/{loan_id}",
    response_model=LoanDetailResponse,
    summary="Consultar un préstamo por ID",
    dependencies=[Depends(get_current_active_user)],
)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    db_loan = loan_service.get_loan_by_id(db, loan_id)
    if not db_loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado.")
    return loan_service.to_loan_detail(db_loan)


@router.patch(
    "/{loan_id}/return",
    response_model=LoanResponse,
    summary="Registrar la devolución de un préstamo",
    response_description="Préstamo marcado como devuelto; el dispositivo vuelve a estar disponible",
    dependencies=[Depends(require_admin_or_support)],
)
def return_loan(loan_id: int, db: Session = Depends(get_db)):
    """
    Marca un préstamo como `returned`, asigna la fecha de devolución y
    vuelve a marcar el dispositivo asociado como disponible.
    """
    db_loan = loan_service.get_loan_by_id(db, loan_id)
    if not db_loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado.")

    if db_loan.status == "returned":
        raise HTTPException(status_code=409, detail="Este préstamo ya fue devuelto.")

    return loan_service.return_loan(db, db_loan)
