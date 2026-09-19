"""Validadores reutilizables entre distintos schemas Pydantic del proyecto."""

import re


def validate_strong_password(value: str) -> str:
    """
    Valida que una contraseña cumpla las reglas mínimas de seguridad:
    - Mínimo 8 caracteres.
    - Al menos una mayúscula.
    - Al menos una minúscula.
    - Al menos un número.
    - Sin espacios en blanco.
    """
    if len(value) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if " " in value:
        raise ValueError("La contraseña no puede contener espacios en blanco.")
    if not re.search(r"[A-Z]", value):
        raise ValueError("La contraseña debe incluir al menos una letra mayúscula.")
    if not re.search(r"[a-z]", value):
        raise ValueError("La contraseña debe incluir al menos una letra minúscula.")
    if not re.search(r"\d", value):
        raise ValueError("La contraseña debe incluir al menos un número.")
    return value
