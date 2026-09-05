from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from app.schemas.user_schema import UserCreate, UserUpdate, UserPatch, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

# Base de datos simulada en memoria
fake_users_db = []
user_id_counter = 1

# Dependency Injection: Función para simular la conexión a una base de datos
def get_db():
    return fake_users_db

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: list = Depends(get_db)):
    global user_id_counter
    # Validar correo repetido
    if any(u["email"] == user.email for u in db):
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")
    
    new_user = user.model_dump() # Pydantic v2
    new_user["id"] = user_id_counter
    db.append(new_user)
    user_id_counter += 1
    return new_user

@router.get("/", response_model=List[UserResponse])
def get_users(role: Optional[str] = None, is_active: Optional[bool] = None, db: list = Depends(get_db)):
    result = db
    # Filtros opcionales
    if role:
        result = [u for u in result if u["role"].lower() == role.lower()]
    if is_active is not None:
        result = [u for u in result if u["is_active"] == is_active]
    return result

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: list = Depends(get_db)):
    user = next((u for u in db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: list = Depends(get_db)):
    existing_user = next((u for u in db if u["id"] == user_id), None)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    # Validar que el nuevo correo no pertenezca a otro usuario
    if any(u["email"] == user.email and u["id"] != user_id for u in db):
        raise HTTPException(status_code=400, detail="El correo ya está registrado por otro usuario.")
    
    existing_user.update(user.model_dump())
    return existing_user

@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(user_id: int, user: UserPatch, db: list = Depends(get_db)):
    existing_user = next((u for u in db if u["id"] == user_id), None)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    # exclude_unset=True ignora los campos que no se enviaron en la petición
    update_data = user.model_dump(exclude_unset=True) 
    
    # Validar PATCH vacío
    if not update_data:
        raise HTTPException(status_code=400, detail="El cuerpo de la petición no puede estar vacío.")
        
    if "email" in update_data and any(u["email"] == update_data["email"] and u["id"] != user_id for u in db):
        raise HTTPException(status_code=400, detail="El correo ya está registrado por otro usuario.")
        
    existing_user.update(update_data)
    return existing_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: list = Depends(get_db)):
    existing_user = next((u for u in db if u["id"] == user_id), None)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    db.remove(existing_user)
    return None