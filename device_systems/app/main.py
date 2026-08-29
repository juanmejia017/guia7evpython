"""
device_systems
--------------
API REST para la gestión de usuarios, desarrollada con FastAPI.

Actividad: GA1-220501096-01-AA1-EV07
Fundamentos de FastAPI: API REST para Gestión de Usuarios.
"""

from fastapi import FastAPI

from app.routes import user_routes

app = FastAPI(
    title="device_systems",
    description=(
        "API REST del sistema device_systems para la gestión del recurso "
        "'usuarios': listado, consulta por ID, filtros por rol/estado y "
        "registro de nuevos usuarios."
    ),
    version="1.0.0",
)

app.include_router(user_routes.router)


@app.get("/", tags=["Root"], summary="Estado del servicio")
def read_root():
    """Endpoint raíz para verificar que la API está en funcionamiento."""
    return {
        "app": "device_systems",
        "status": "ok",
        "docs": "/docs",
    }
