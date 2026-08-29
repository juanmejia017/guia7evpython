"""
Endpoints del recurso 'usuarios' para device_systems.

Incluye:
- GET /users              -> listar todos (con filtros opcionales por query params)
- GET /users/{user_id}    -> consultar un usuario por path parameter
- POST /users             -> registrar un nuevo usuario
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Path, Response, status

from app.schemas.user_schema import UserCreate, UserResponse, UserRole

router = APIRouter(prefix="/users", tags=["Usuarios"])

# "Base de datos" en memoria para fines didácticos.
# Cada elemento combina los campos de UserCreate + un id autoincremental.
fake_users_db: list[dict] = [
    {
        "id": 1,
        "name": "Juan Mejía",
        "email": "juan.mejia@example.com",
        "role": UserRole.admin,
        "is_active": True,
    },
    {
        "id": 2,
        "name": "Laura Gómez",
        "email": "laura.gomez@example.com",
        "role": UserRole.support,
        "is_active": True,
    },
    {
        "id": 3,
        "name": "Carlos Ríos",
        "email": "carlos.rios@example.com",
        "role": UserRole.user,
        "is_active": False,
    },
]


def _next_id() -> int:
    """Calcula el siguiente id disponible en la base de datos simulada."""
    if not fake_users_db:
        return 1
    return max(user["id"] for user in fake_users_db) + 1


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar usuarios",
    description="Lista todos los usuarios. Permite filtrar opcionalmente por rol y por estado activo.",
)
def list_users(
    response: Response,
    role: Optional[UserRole] = Query(
        default=None, description="Filtra usuarios por rol: admin, support o user."
    ),
    is_active: Optional[bool] = Query(
        default=None, description="Filtra usuarios por estado activo (true/false)."
    ),
):
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"

    results = fake_users_db

    if role is not None:
        results = [user for user in results if user["role"] == role]

    if is_active is not None:
        results = [user for user in results if user["is_active"] == is_active]

    return results


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar usuario por ID",
    description="Retorna un único usuario a partir de su identificador (path parameter).",
)
def get_user(
    response: Response,
    user_id: int = Path(..., gt=0, description="Identificador del usuario a consultar."),
):
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"

    for user in fake_users_db:
        if user["id"] == user_id:
            return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Usuario con id {user_id} no encontrado.",
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    description="Crea un nuevo usuario validando los datos de entrada y evitando correos duplicados.",
)
def create_user(user: UserCreate, response: Response):
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"

    email_exists = any(
        existing["email"].lower() == user.email.lower() for existing in fake_users_db
    )
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario registrado con el correo {user.email}.",
        )

    new_user = {
        "id": _next_id(),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }
    fake_users_db.append(new_user)

    return new_user
