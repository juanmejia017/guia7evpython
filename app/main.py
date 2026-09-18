from fastapi import FastAPI, Request

from app.routes.user_routes import router as user_router

# A partir de esta versión, el esquema de la base de datos ya no se crea con
# Base.metadata.create_all(): se gestiona mediante migraciones versionadas
# con Alembic. Antes de levantar el servidor por primera vez (o tras
# modificar un modelo), ejecuta:
#   alembic upgrade head

app = FastAPI(
    title="device_systems API",
    description="API REST para la gestión de usuarios, dispositivos y préstamos, con persistencia en base de datos mediante SQLAlchemy y migraciones versionadas con Alembic.",
    version="3.0.0"
)

# Middleware opcional para cabeceras personalizadas
@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "3.0"
    return response

# Ruta raíz para evitar el error 404 al entrar a http://127.0.0.1:8000/
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenido a device_systems API. Ve a /docs para ver la documentación interactiva."}

# Incluir las rutas del CRUD de usuarios
app.include_router(user_router)