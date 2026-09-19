from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth_service import authenticate_user, generate_token_for_user
from app.dependencies.auth_dependency import get_current_user
from app.dependencies.database_dependency import get_db
from app.rate_limiter import limiter
from app.schemas.auth_schema import Token, UserRegister
from app.schemas.user_schema import UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    response_description="Usuario creado (sin exponer la contraseña ni su hash)",
)
@limiter.limit("3/minute")
def register(request: Request, user: UserRegister, db: Session = Depends(get_db)):
    """
    Crea una cuenta de usuario con contraseña segura (hasheada con bcrypt
    antes de guardarse). Valida que el correo no esté ya registrado.

    Límite: 3 solicitudes por minuto por IP.
    """
    if user_service.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")

    # Reutiliza user_service.create_user, que ya hashea la contraseña,
    # construyendo un UserCreate equivalente a partir de UserRegister.
    user_create = UserCreate(
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role,
        is_active=True,
    )
    return user_service.create_user(db, user_create)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión y obtener un token JWT",
    response_description="Token de acceso (Bearer) válido para las rutas protegidas",
)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Autentica al usuario usando `username` (correo) y `password` del
    formulario OAuth2 estándar, y retorna un token JWT de tipo `bearer`.

    Límite: 5 solicitudes por minuto por IP.
    """
    db_user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = generate_token_for_user(db_user)
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Consultar los datos del usuario autenticado",
)
def read_current_user(current_user=Depends(get_current_user)):
    """Retorna los datos del usuario dueño del token enviado (sin la contraseña)."""
    return current_user
