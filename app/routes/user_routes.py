from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.schemas.user_schema import RoleEnum, UserCreate, UserPatch, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Validar correo repetido
    if user_service.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")
    return user_service.create_user(db, user)


@router.get("/", response_model=List[UserResponse])
def get_users(
    role: Optional[RoleEnum] = None,
    is_active: Optional[bool] = None,
    order_by: Optional[str] = Query(
        None, description="Orden: name, -name, created_at, -created_at"
    ),
    db: Session = Depends(get_db),
):
    return user_service.get_users(
        db, role=role.value if role else None, is_active=is_active, order_by=order_by
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Validar que el nuevo correo no pertenezca a otro usuario
    other_user = user_service.get_user_by_email(db, user.email)
    if other_user and other_user.id != user_id:
        raise HTTPException(status_code=400, detail="El correo ya está registrado por otro usuario.")

    return user_service.update_user(db, db_user, user)


@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(user_id: int, user: UserPatch, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # exclude_unset=True ignora los campos que no se enviaron en la petición
    update_data = user.model_dump(exclude_unset=True)

    # Validar PATCH vacío
    if not update_data:
        raise HTTPException(status_code=400, detail="El cuerpo de la petición no puede estar vacío.")

    if "email" in update_data:
        other_user = user_service.get_user_by_email(db, update_data["email"])
        if other_user and other_user.id != user_id:
            raise HTTPException(status_code=400, detail="El correo ya está registrado por otro usuario.")

    return user_service.patch_user(db, db_user, user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    user_service.delete_user(db, db_user)
    return None
