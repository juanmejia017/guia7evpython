"""
Configuración de la conexión a la base de datos para device_systems.

Se utiliza SQLite como motor de base de datos para el desarrollo inicial.
Este módulo expone:
    - engine: motor de conexión a la base de datos.
    - SessionLocal: fábrica de sesiones para interactuar con la base de datos.
    - Base: clase base declarativa de la cual heredan los modelos SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# connect_args es necesario únicamente para SQLite, ya que por defecto
# solo permite el uso del mismo hilo que creó la conexión.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Fábrica de sesiones: cada instancia representa una conversación con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la cual heredarán todos los modelos SQLAlchemy
Base = declarative_base()
