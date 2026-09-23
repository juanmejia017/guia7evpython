"""
Middleware personalizado para device_systems.

Agrega, a cada respuesta:
    - `X-App-Name`: nombre de la aplicación.
    - `X-Process-Time`: tiempo de procesamiento de la petición, en segundos.
    - `X-Request-ID`: identificador único de la petición (se genera uno
      nuevo o se propaga el recibido en el header `X-Request-ID` del
      cliente, útil para trazabilidad entre servicios).

Además, registra en el logger de la aplicación el método, la ruta y el
código de estado de cada petición procesada.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("device_systems")
logging.basicConfig(level=logging.INFO)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Mide tiempo de respuesta, agrega cabeceras y registra cada petición."""

    async def dispatch(self, request: Request, call_next):
        # Propaga el X-Request-ID recibido, o genera uno nuevo
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:8])

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        response.headers["X-App-Name"] = "device_systems"
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "method=%s path=%s status_code=%s request_id=%s process_time=%.4fs",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            process_time,
        )

        return response
