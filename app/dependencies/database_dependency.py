"""
Dependencia de FastAPI encargada de entregar una sesión de base de datos
a cada endpoint que la necesite, cerrándola automáticamente al finalizar
la petición.
"""

from app.database.connection import SessionLocal


def get_db():
    """Provee una sesión de base de datos y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
