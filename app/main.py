from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.auth.auth_routes import router as auth_router
from app.config import CORS_ALLOWED_ORIGINS
from app.middlewares.request_middleware import RequestContextMiddleware
from app.rate_limiter import limiter
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router
from app.routes.user_routes import router as user_router

# A partir de esta versión, el esquema de la base de datos ya no se crea con
# Base.metadata.create_all(): se gestiona mediante migraciones versionadas
# con Alembic. Antes de levantar el servidor por primera vez (o tras
# modificar un modelo), ejecuta:
#   alembic upgrade head

app = FastAPI(
    title="device_systems API",
    description="API REST segura para gestión de usuarios, dispositivos y préstamos, con autenticación OAuth2/JWT, rate limiting y CORS.",
    version="4.0.0",
)

# --- Rate limiting (slowapi) ---
# app.state.limiter debe registrarse ANTES de que las rutas decoradas con
# @limiter.limit(...) se ejecuten; el exception handler traduce los excesos
# de límite a una respuesta 429 Too Many Requests.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- CORS ---
# En desarrollo se permite un conjunto explícito de orígenes locales
# (configurables vía CORS_ALLOWED_ORIGINS en .env). NUNCA se debe usar
# allow_origins=["*"] junto con allow_credentials=True: el propio estándar
# CORS lo prohíbe (los navegadores lo rechazan), y aunque se lograra evadir,
# significaría aceptar cookies/credenciales desde CUALQUIER sitio web,
# exponiendo la API a ataques CSRF y robo de sesión. Por eso se declara una
# lista blanca explícita de orígenes confiables.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware personalizado (trazabilidad, tiempos, cabeceras) ---
app.add_middleware(RequestContextMiddleware)


# Ruta raíz para evitar el error 404 al entrar a http://127.0.0.1:8000/
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenido a device_systems API. Ve a /docs para ver la documentación interactiva."}


@app.get("/security/policy", tags=["Security"], summary="Consultar la política de seguridad de la API")
def security_policy():
    """
    Expone, de forma pública, un resumen no sensible de los mecanismos de
    seguridad activos en la API (sin revelar secretos): algoritmo de firma
    JWT, duración del token, orígenes CORS permitidos y límites de tasa
    configurados.
    """
    return {
        "authentication": "OAuth2 Password Flow + JWT (Bearer token)",
        "jwt_algorithm": "HS256",
        "password_hashing": "bcrypt (via passlib)",
        "cors_allowed_origins": CORS_ALLOWED_ORIGINS,
        "rate_limits": {
            "POST /auth/login": "5/minute",
            "POST /auth/register": "3/minute",
            "GET /users": "30/minute",
            "POST /loans": "10/minute",
        },
    }


# Incluir las rutas de auth, users, devices y loans
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)