# device_systems

API REST desarrollada con **FastAPI** para la gestión del recurso **usuarios**
dentro del sistema `device_systems`.

Proyecto realizado para la actividad **GA1-220501096-01-AA1-EV07 – Fundamentos
de FastAPI: API REST para Gestión de Usuarios** (SENA, ADSO).

## Descripción de la aplicación

`device_systems` expone un API REST que permite:

- Listar usuarios, con filtros opcionales por `role` y `is_active`.
- Consultar un usuario puntual mediante su `id` (path parameter).
- Registrar nuevos usuarios, validando los datos con **Pydantic v2** y
  evitando correos duplicados.
- Retornar respuestas estandarizadas mediante `response_model`, ocultando
  cualquier dato interno que no deba exponerse.
- Enviar cabeceras HTTP personalizadas en cada respuesta:
  - `X-App-Name: device_systems`
  - `X-API-Version: 1.0`

## Estructura del proyecto

```
device_systems/
│── app/
│   │── main.py
│   │── schemas/
│   │   │── user_schema.py
│   │── routes/
│   │   │── user_routes.py
│── requirements.txt
│── README.md
```

## Modelo de usuario

| Campo       | Tipo    | Validación                                   |
|-------------|---------|-----------------------------------------------|
| `id`        | int     | Autogenerado por el servidor                  |
| `name`      | str     | Obligatorio, mínimo 3 caracteres               |
| `email`     | EmailStr| Formato de correo válido y único               |
| `role`      | enum    | `admin`, `support` o `user`                    |
| `is_active` | bool    | `true` o `false`                               |

## Instalación de dependencias

1. Clonar el repositorio y ubicarse en la carpeta del proyecto:

   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd device_systems
   ```

2. Crear y activar un entorno virtual (opcional pero recomendado):

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux / macOS
   source .venv/bin/activate
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

## Ejecución del servidor

Desde la raíz del proyecto (`device_systems/`):

```bash
uvicorn app.main:app --reload
```

La API quedará disponible en `http://127.0.0.1:8000` y la documentación
interactiva (Swagger UI) en `http://127.0.0.1:8000/docs`.

## Tabla de endpoints

| Método | Endpoint             | Descripción                                    |
|--------|-----------------------|-------------------------------------------------|
| GET    | `/`                    | Verifica el estado del servicio                |
| GET    | `/users`               | Lista todos los usuarios                        |
| GET    | `/users?role=admin`    | Filtra usuarios por rol                         |
| GET    | `/users?is_active=true`| Filtra usuarios por estado activo/inactivo      |
| GET    | `/users/{user_id}`     | Consulta un usuario por su ID                   |
| POST   | `/users`                | Registra un nuevo usuario                       |

## Ejemplos de peticiones

### GET /users

```bash
curl -X GET "http://127.0.0.1:8000/users"
```

Respuesta:

```json
[
  {
    "id": 1,
    "name": "Juan Mejía",
    "email": "juan.mejia@example.com",
    "role": "admin",
    "is_active": true
  }
]
```

### GET /users/{user_id}

```bash
curl -X GET "http://127.0.0.1:8000/users/1"
```

### GET /users?role=admin&is_active=true

```bash
curl -X GET "http://127.0.0.1:8000/users?role=admin&is_active=true"
```

### POST /users

```bash
curl -X POST "http://127.0.0.1:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "María Torres",
        "email": "maria.torres@example.com",
        "role": "user",
        "is_active": true
      }'
```

Respuesta (`201 Created`):

```json
{
  "id": 4,
  "name": "María Torres",
  "email": "maria.torres@example.com",
  "role": "user",
  "is_active": true
}
```

### Error por correo duplicado (`400 Bad Request`)

```bash
curl -X POST "http://127.0.0.1:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "Otro Usuario",
        "email": "juan.mejia@example.com",
        "role": "user",
        "is_active": true
      }'
```

```json
{
  "detail": "Ya existe un usuario registrado con el correo juan.mejia@example.com."
}
```

## Capturas de Swagger UI

> Agregar aquí las capturas de pantalla de `http://127.0.0.1:8000/docs`
> mostrando las pruebas de:
> - `GET /users`
> - `GET /users/{user_id}`
> - `POST /users`
> - Un caso de validación/error (por ejemplo, correo duplicado o `name`
>   con menos de 3 caracteres).

## Reflexión sobre el uso de FastAPI

FastAPI permite construir APIs REST de forma rápida y segura gracias a su
integración nativa con Pydantic para la validación de datos, la generación
automática de documentación interactiva (Swagger UI) y el manejo declarativo
de path/query parameters. En este proyecto se aplicaron modelos de entrada y
salida separados (`UserCreate` / `UserResponse`) para controlar exactamente
qué información se expone al cliente, además de cabeceras HTTP personalizadas
y manejo de errores mediante `HTTPException`.
