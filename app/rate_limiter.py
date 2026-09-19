"""
Instancia compartida de `Limiter` (slowapi) usada para aplicar rate
limiting en distintas rutas. Se define en un módulo aparte para que tanto
`main.py` como los routers puedan importarla sin generar dependencias
circulares.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
