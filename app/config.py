"""
Configuración centralizada de la aplicación, cargada desde variables de
entorno (archivo `.env`) mediante python-dotenv.

Mantener los secretos (SECRET_KEY, etc.) fuera del código fuente es una
buena práctica de seguridad: el archivo `.env` real nunca se sube al
repositorio (ver `.gitignore`); solo se versiona `.env.example` como
plantilla.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# --- Seguridad / JWT ---
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-default-secret-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# --- CORS ---
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]

# --- Base de datos ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./device_systems.db")
