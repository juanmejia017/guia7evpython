# device_systems

API REST desarrollada con **FastAPI**, **SQLAlchemy**, **Alembic** y una capa
de **seguridad** (OAuth2 + JWT, hashing de contraseñas, CORS, middleware
personalizado y rate limiting) para la gestión de **usuarios**,
**dispositivos** y **préstamos** dentro del sistema `device_systems`.

Proyecto realizado para las actividades:
- **GA1-220501096-01-AA1-EV07 – Fundamentos de FastAPI: API REST para Gestión de Usuarios** (SENA, ADSO).
- **GA1-220501096-01-AA1-EV09 – FastAPI con SQLAlchemy: Persistencia de Datos y CRUD sobre Base de Datos** (SENA, ADSO).
- **GA1-220501096-01-AA1-EV10 – FastAPI Avanzado: Migraciones con Alembic, Asociaciones de Modelos y Consultas con Joins** (SENA, ADSO).
- **GA1-220501096-01-AA1-EV11 – FastAPI Seguridad: Autenticación, Middleware, CORS, Rate Limiting y Validación Avanzada** (SENA, ADSO).

## Descripción de la aplicación

`device_systems` expone un API REST que permite:

- Registrar y autenticar usuarios mediante **OAuth2 + JWT** (`/auth/register`, `/auth/login`, `/auth/me`), con contraseñas hasheadas (bcrypt) que nunca se guardan ni se exponen en texto plano.
- Proteger rutas sensibles según el usuario esté **autenticado** o tenga un **rol específico** (`admin`, `support`, `user`), devolviendo `401` (sin token/token inválido) o `403` (sin permisos) según corresponda.
- Gestionar usuarios (`/users`), dispositivos (`/devices`) y préstamos (`/loans`) con CRUD completo donde aplica, con filtros, orden y consultas con `join()`.
- Registrar préstamos, validando que el usuario y el dispositivo existan y que el dispositivo esté disponible; al prestarlo, el dispositivo queda marcado como no disponible. Al devolverlo, vuelve a estar disponible.
- Limitar el número de peticiones por IP en endpoints sensibles (**rate limiting** con `slowapi`), respondiendo `429 Too Many Requests` si se supera el límite.
- Restringir los orígenes que pueden consumir la API desde un navegador (**CORS**) mediante una lista blanca explícita.
- Agregar trazabilidad a cada petición mediante un **middleware personalizado** (tiempo de respuesta, `X-Request-ID`, logging).
- Persistir todos los datos en una base de datos **SQLite** mediante el ORM **SQLAlchemy**, versionando los cambios de esquema con **Alembic**.
- Retornar respuestas estandarizadas mediante `response_model`, ocultando cualquier dato interno (como `hashed_password`) que no deba exponerse.

## Estructura del proyecto

```text
device_systems/
├── app/
│   ├── main.py
│   ├── config.py               # Carga variables de entorno (.env)
│   ├── rate_limiter.py         # Instancia compartida de Limiter (slowapi)
│   ├── auth/
│   │   ├── security.py         # Hash de contraseñas y JWT (crear/validar)
│   │   ├── auth_service.py     # authenticate_user(), generate_token_for_user()
│   │   └── auth_routes.py      # /auth/register, /auth/login, /auth/me
│   ├── database/
│   │   └── connection.py       # engine, SessionLocal y Base declarativa
│   ├── models/
│   │   ├── user_model.py       # incluye hashed_password
│   │   ├── device_model.py
│   │   └── loan_model.py
│   ├── schemas/
│   │   ├── user_schema.py
│   │   ├── device_schema.py
│   │   ├── loan_schema.py
│   │   ├── auth_schema.py      # UserRegister, UserLogin, Token, TokenData
│   │   └── validators.py       # Validación reutilizable de contraseña fuerte
│   ├── routes/
│   │   ├── user_routes.py      # Protegidas con Depends(get_current_active_user) / require_admin
│   │   ├── device_routes.py    # Protegidas con require_admin_or_support / require_admin
│   │   └── loan_routes.py      # Protegidas con autenticación y rol
│   ├── services/
│   │   ├── user_service.py
│   │   ├── device_service.py
│   │   └── loan_service.py
│   ├── dependencies/
│   │   ├── database_dependency.py
│   │   └── auth_dependency.py  # get_current_user, get_current_active_user, require_roles
│   └── middlewares/
│       └── request_middleware.py  # X-Process-Time, X-Request-ID, logging
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── .env                # NO se sube al repo (ver .gitignore)
├── .env.example        # Plantilla de variables de entorno
├── requirements.txt
└── README.md
```

## Modelo SQLAlchemy vs. schemas Pydantic

El **modelo SQLAlchemy** (`app/models/user_model.py`) define la estructura real
de la tabla `users` en la base de datos, incluyendo sus restricciones a nivel
de columna:

| Campo        | Tipo SQLAlchemy | Restricción                              |
|--------------|------------------|-------------------------------------------|
| `id`         | Integer          | Primary Key, index                        |
| `name`       | String(50)       | `nullable=False`                          |
| `email`      | String           | `unique=True`, `nullable=False`, index    |
| `role`       | String           | `nullable=False`                          |
| `is_active`  | Boolean          | `default=True`, `nullable=False`          |
| `created_at` | DateTime         | `default=datetime.utcnow`, `nullable=False` |

Los **schemas Pydantic** (`app/schemas/user_schema.py`) son independientes del
modelo de base de datos y controlan la validación de entrada y el formato de
salida de la API:

| Schema         | Uso                                    | Validaciones                                                    |
|----------------|-----------------------------------------|-------------------------------------------------------------------|
| `UserCreate`   | Cuerpo de `POST /users`                | `name` (mín. 3 car.), `email` (formato válido), `role` (enum)    |
| `UserUpdate`   | Cuerpo de `PUT /users/{id}`            | Igual a `UserCreate`, reemplazo completo                          |
| `UserPatch`    | Cuerpo de `PATCH /users/{id}`          | Todos los campos opcionales                                       |
| `UserResponse` | Respuesta de la API                    | Incluye `id` y `created_at` generados por la base de datos        |

El campo `role` se valida contra el enum `RoleEnum`, que solo admite los
valores `admin`, `support` o `user`.

### Modelo `Device`

| Campo           | Tipo SQLAlchemy | Restricción                              |
|-----------------|------------------|-------------------------------------------|
| `id`            | Integer          | Primary Key, index                        |
| `name`          | String(100)      | `nullable=False`                          |
| `serial_number` | String           | `unique=True`, `nullable=False`, index    |
| `device_type`   | String           | `nullable=False` (enum: laptop, tablet, proyector, camara, router, monitor) |
| `brand`         | String           | Opcional                                  |
| `is_available`  | Boolean          | `default=True`, `nullable=False`          |
| `created_at`    | DateTime         | `default=datetime.utcnow`, `nullable=False` |

### Modelo `Loan`

| Campo         | Tipo SQLAlchemy | Restricción                                      |
|---------------|------------------|----------------------------------------------------|
| `id`          | Integer          | Primary Key, index                                 |
| `user_id`     | Integer          | `ForeignKey("users.id")`, `nullable=False`, index   |
| `device_id`   | Integer          | `ForeignKey("devices.id")`, `nullable=False`, index |
| `loan_date`   | DateTime         | `default=datetime.utcnow`, `nullable=False`         |
| `return_date` | DateTime         | Opcional (se asigna al devolver el dispositivo)     |
| `status`      | String           | `nullable=False` (`active`, `returned`, `overdue`)  |

## Asociaciones entre modelos

Las relaciones se definen con `relationship()` y `back_populates()`:

- **User ↔ Loan** (uno a muchos): un usuario puede tener muchos préstamos (`User.loans`), y cada préstamo pertenece a un único usuario (`Loan.user`).
- **Device ↔ Loan** (uno a muchos): un dispositivo puede aparecer en muchos préstamos históricos (`Device.loans`), y cada préstamo referencia un único dispositivo (`Loan.device`).
- La integridad referencial se garantiza mediante `ForeignKey("users.id")` y `ForeignKey("devices.id")` en el modelo `Loan`.

## Seguridad: autenticación, autorización y protección de la API

### Variables de entorno (`.env`)

Los secretos (clave JWT, orígenes CORS, URL de base de datos) se cargan desde
un archivo `.env` mediante `python-dotenv` (ver `app/config.py`). El archivo
`.env` real **no se sube al repositorio** (está en `.gitignore`); en su lugar
se versiona `.env.example` como plantilla:

```env
SECRET_KEY=change-this-secret-key-for-a-real-random-value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
DATABASE_URL=sqlite:///./device_systems.db
```

Antes de correr el proyecto, copia `.env.example` como `.env` y genera tu
propia `SECRET_KEY` (por ejemplo con `python -c "import secrets; print(secrets.token_hex(32))"`).

### Hash de contraseñas (passlib + bcrypt)

Ninguna contraseña se guarda ni se muestra en texto plano. `app/auth/security.py`
usa `passlib.context.CryptContext` con el esquema `bcrypt` para:

- `get_password_hash(password)`: genera el hash antes de guardar el usuario.
- `verify_password(plain_password, hashed_password)`: compara la contraseña ingresada en el login contra el hash almacenado.

El campo `hashed_password` del modelo `User` nunca aparece en `UserResponse`
ni en ningún schema de salida.

### Autenticación OAuth2 + JWT

- `POST /auth/register`: crea una cuenta validando nombre, correo único, contraseña segura y rol permitido. Devuelve el usuario creado (sin contraseña).
- `POST /auth/login`: recibe `username` (correo) y `password` mediante el formulario estándar `OAuth2PasswordRequestForm`, verifica la contraseña y retorna un token JWT (`access_token`, `token_type: "bearer"`).
- `GET /auth/me`: retorna los datos del usuario dueño del token enviado en `Authorization: Bearer <token>`.

El token se firma con `python-jose` (`create_access_token`) usando `SECRET_KEY`
y el algoritmo `HS256`, con expiración configurable (`ACCESS_TOKEN_EXPIRE_MINUTES`,
30 minutos por defecto). `decode_access_token` valida la firma y expiración al
recibir cada petición protegida.

### Protección de rutas por rol

`app/dependencies/auth_dependency.py` expone:

- `get_current_user`: decodifica el token y busca el usuario; `401 Unauthorized` si el token falta, es inválido o expiró.
- `get_current_active_user`: además exige que el usuario esté activo.
- `require_roles(*roles)` (y sus atajos `require_admin`, `require_admin_or_support`): `403 Forbidden` si el usuario autenticado no tiene el rol requerido.

Rutas protegidas:

| Ruta                          | Protección requerida     |
|--------------------------------|---------------------------|
| `GET /users`                  | Usuario autenticado       |
| `GET /users/{user_id}`        | Usuario autenticado       |
| `POST /users`, `PUT`, `PATCH`, `DELETE /users/{id}` | Admin |
| `POST /devices`               | Admin o support            |
| `PUT /devices/{device_id}`    | Admin o support            |
| `PATCH /devices/{device_id}`  | Admin o support            |
| `DELETE /devices/{device_id}` | Admin                      |
| `POST /loans`                 | Usuario autenticado        |
| `GET /loans`, `GET /loans/details` | Admin o support        |
| `GET /loans/{loan_id}`        | Usuario autenticado        |
| `PATCH /loans/{loan_id}/return` | Admin o support           |

### CORS

`main.py` configura `CORSMiddleware` con una lista blanca explícita de
orígenes (`CORS_ALLOWED_ORIGINS` en `.env`, por defecto `http://localhost:5173`
y `http://localhost:3000`), `allow_credentials=True`, `allow_methods=["*"]` y
`allow_headers=["*"]`.

**¿Por qué no usar `allow_origins=["*"]` en producción cuando hay credenciales?**
La especificación CORS prohíbe combinar `allow_origins=["*"]` con
`allow_credentials=True` (el propio navegador rechaza esa combinación), porque
equivaldría a aceptar peticiones autenticadas, con cookies o headers de
autorización, desde **cualquier sitio web**, no solo desde el frontend propio.
Esto abre la puerta a ataques CSRF y a que un sitio malicioso use la sesión de
un usuario para actuar en su nombre. Por eso se declara una lista explícita de
orígenes confiables, y se recomienda que en producción `CORS_ALLOWED_ORIGINS`
contenga únicamente el dominio real del frontend (ej. `https://miapp.com`).

### Middleware personalizado

`app/middlewares/request_middleware.py` agrega a cada respuesta:

- `X-App-Name: device_systems`
- `X-Process-Time`: tiempo de procesamiento de la petición, en segundos.
- `X-Request-ID`: identificador único de la petición (se genera o se propaga si el cliente ya envió uno), útil para trazabilidad y depuración.

Además, registra en el logger de la aplicación el método, la ruta, el código
de estado y el tiempo de cada petición procesada.

### Rate limiting (slowapi)

`app/rate_limiter.py` define una instancia compartida de `Limiter`. Los
límites configurados son:

| Endpoint              | Límite                  |
|------------------------|--------------------------|
| `POST /auth/login`     | 5 solicitudes / minuto   |
| `POST /auth/register`  | 3 solicitudes / minuto   |
| `GET /users`           | 30 solicitudes / minuto  |
| `POST /loans`          | 10 solicitudes / minuto  |

Al superar el límite, la API responde `429 Too Many Requests` con un cuerpo
como `{"error": "Rate limit exceeded: 3 per 1 minute"}`. Esto se verificó
realizando peticiones repetidas contra `/auth/register` y `POST /loans` (ver
sección de pruebas funcionales).

## Migraciones con Alembic

El esquema de la base de datos se gestiona con **Alembic** en lugar de `Base.metadata.create_all()`. `alembic/env.py` importa la `Base` y los modelos de `app/` para que `--autogenerate` detecte los cambios.

Comandos principales:

```bash
# Generar una nueva migración a partir de cambios en los modelos
alembic revision --autogenerate -m "mensaje descriptivo"

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Ver el historial de migraciones
alembic history

# Revertir la última migración
alembic downgrade -1
```

La migración inicial (`create devices and loans tables`) crea las tablas `users`, `devices` y `loans` junto con sus índices y llaves foráneas.

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

4. Configurar las variables de entorno:

   ```bash
   cp .env.example .env
   # Edita .env y reemplaza SECRET_KEY por un valor propio, por ejemplo:
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

## Ejecución del servidor

Desde la raíz del proyecto (`device_systems/`):

```bash
# 1. Aplicar las migraciones (crea/actualiza el esquema de la base de datos)
alembic upgrade head

# 2. Levantar el servidor
uvicorn app.main:app --reload
```

A partir de esta versión, el esquema **ya no se crea automáticamente** con
`Base.metadata.create_all()`: se gestiona mediante migraciones versionadas
con Alembic, por lo que `alembic upgrade head` es un paso obligatorio antes
de levantar el servidor por primera vez (o después de modificar un modelo).

La API quedará disponible en `http://127.0.0.1:8000` y la documentación interactiva (Swagger UI) en `http://127.0.0.1:8000/docs`.

## Tabla de endpoints

### Auth

| Método | Endpoint         | Descripción                                                   | Rate limit  |
|--------|-------------------|----------------------------------------------------------------|-------------|
| POST   | `/auth/register`  | Registra un usuario con contraseña segura (hash bcrypt)        | 3/minuto    |
| POST   | `/auth/login`      | Autentica y retorna un token JWT (`access_token`, `bearer`)    | 5/minuto    |
| GET    | `/auth/me`         | Retorna los datos del usuario dueño del token (requiere token) | —           |

### Users

| Método | Endpoint                | Descripción                                     |
|--------|--------------------------|-------------------------------------------------|
| GET    | `/`                      | Verifica el estado del servicio                 |
| GET    | `/users`                 | Lista todos los usuarios                        |
| GET    | `/users?role=admin`      | Filtra usuarios por rol                         |
| GET    | `/users?is_active=true`  | Filtra usuarios por estado activo/inactivo      |
| GET    | `/users?order_by=-name`  | Ordena por `name`, `-name`, `created_at` o `-created_at` |
| GET    | `/users/{user_id}`       | Consulta un usuario por su ID                   |
| GET    | `/users/{user_id}/loans` | Consulta los préstamos de un usuario (join)     |
| POST   | `/users`                 | Registra un nuevo usuario                       |
| PUT    | `/users/{user_id}`       | Actualiza completamente un usuario existente    |
| PATCH  | `/users/{user_id}`       | Actualiza parcialmente los datos de un usuario  |
| DELETE | `/users/{user_id}`       | Elimina un usuario del sistema                  |

### Devices

| Método | Endpoint                          | Descripción                                       |
|--------|------------------------------------|----------------------------------------------------|
| GET    | `/devices`                        | Lista todos los dispositivos                        |
| GET    | `/devices?device_type=laptop`     | Filtra por tipo de dispositivo                       |
| GET    | `/devices?is_available=true`      | Filtra por disponibilidad                            |
| GET    | `/devices?brand=lenovo`           | Filtra por marca (coincidencia parcial)              |
| GET    | `/devices?search=thinkpad`        | Búsqueda libre por nombre, serie o marca (`ilike`)   |
| GET    | `/devices/{device_id}`            | Consulta un dispositivo por su ID                    |
| GET    | `/devices/{device_id}/loans`      | Consulta el historial de préstamos del dispositivo (join) |
| POST   | `/devices`                        | Registra un nuevo dispositivo                        |
| PUT    | `/devices/{device_id}`            | Actualiza completamente un dispositivo               |
| PATCH  | `/devices/{device_id}`            | Actualiza parcialmente un dispositivo                |
| DELETE | `/devices/{device_id}`            | Elimina un dispositivo                               |

### Loans

| Método | Endpoint                          | Descripción                                                    |
|--------|------------------------------------|-----------------------------------------------------------------|
| GET    | `/loans`                          | Lista préstamos con datos de usuario y dispositivo (join)       |
| GET    | `/loans/details`                  | Igual a `/loans`, pensado para consultas explícitas con detalle |
| GET    | `/loans?status=active`            | Filtra préstamos por estado                                     |
| GET    | `/loans?user_id=1`                | Filtra préstamos por usuario                                    |
| GET    | `/loans?device_id=1`              | Filtra préstamos por dispositivo                                |
| GET    | `/loans?user_email=ana@sena.edu.co` | Filtra por correo del usuario (coincidencia parcial)           |
| GET    | `/loans?device_type=laptop`       | Filtra por tipo de dispositivo prestado                         |
| GET    | `/loans/{loan_id}`                | Consulta un préstamo por su ID (con datos relacionados)         |
| POST   | `/loans`                          | Crea un préstamo (valida usuario, dispositivo y disponibilidad) |
| PATCH  | `/loans/{loan_id}/return`         | Marca el préstamo como devuelto y libera el dispositivo         |

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
curl -X POST "http://127.0.0.1:8000/users"   -H "Content-Type: application/json"   -d '{
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

### PUT /users/{user_id} (Actualización completa)

```bash
curl -X PUT "http://127.0.0.1:8000/users/1"   -H "Content-Type: application/json"   -d '{
        "name": "Juan Diego",
        "email": "juan.diego@example.com",
        "role": "admin",
        "is_active": true
      }'
```

### PATCH /users/{user_id} (Actualización parcial)

```bash
curl -X PATCH "http://127.0.0.1:8000/users/1"   -H "Content-Type: application/json"   -d '{
        "is_active": false
      }'
```

### DELETE /users/{user_id}

```bash
curl -X DELETE "http://127.0.0.1:8000/users/1"
```
*(Respuesta: `204 No Content` - Sin cuerpo de respuesta)*

### Error por correo duplicado (`400 Bad Request`)

```bash
curl -X POST "http://127.0.0.1:8000/users"   -H "Content-Type: application/json"   -d '{
        "name": "Otro Usuario",
        "email": "maria.torres@example.com",
        "role": "user",
        "is_active": true
      }'
```

```json
{
  "detail": "Ya existe un usuario registrado con el correo maria.torres@example.com."
}
```

### POST /devices

```bash
curl -X POST "http://127.0.0.1:8000/devices" -H "Content-Type: application/json" -d '{
      "name": "Laptop Lenovo ThinkPad",
      "serial_number": "LEN-2024-001",
      "device_type": "laptop",
      "brand": "Lenovo",
      "is_available": true
    }'
```

### POST /loans (crear un préstamo)

```bash
curl -X POST "http://127.0.0.1:8000/loans" -H "Content-Type: application/json" -d '{
      "user_id": 1,
      "device_id": 1
    }'
```

Si el dispositivo ya está prestado, la API responde `409 Conflict`:

```json
{
  "detail": "El dispositivo no está disponible para préstamo."
}
```

### GET /loans/details (consulta con join)

```bash
curl -X GET "http://127.0.0.1:8000/loans/details?status=active"
```

Respuesta:

```json
[
  {
    "loan_id": 1,
    "status": "active",
    "loan_date": "2026-01-01T10:00:00",
    "return_date": null,
    "user": { "id": 1, "name": "Ana Pérez", "email": "ana@sena.edu.co" },
    "device": { "id": 1, "name": "Laptop Lenovo ThinkPad", "serial_number": "LEN-2024-001", "device_type": "laptop" }
  }
]
```

### PATCH /loans/{loan_id}/return (devolución)

```bash
curl -X PATCH "http://127.0.0.1:8000/loans/1/return"
```

Si el préstamo ya había sido devuelto, la API responde `409 Conflict`:

```json
{
  "detail": "Este préstamo ya fue devuelto."
}
```

## Códigos de estado usados

- **200 OK:** Petición procesada correctamente (GET, PUT, PATCH, incluida la devolución de un préstamo).
- **201 Created:** Registro creado de forma exitosa (POST de usuarios, dispositivos, préstamos o registro en `/auth/register`).
- **204 No Content:** Usuario o dispositivo eliminado correctamente (DELETE).
- **400 Bad Request:** Error del cliente (ej. correo o número de serie duplicado, envío de datos inválidos, PATCH vacío, o login/registro con correo repetido).
- **401 Unauthorized:** No se envió token, el token es inválido, o la contraseña de login es incorrecta.
- **403 Forbidden:** El usuario está autenticado pero su rol no tiene permiso para la operación (ej. un `user` intentando crear un dispositivo).
- **404 Not Found:** Recurso no encontrado (ej. usuario, dispositivo o préstamo inexistente).
- **409 Conflict:** Regla de negocio incumplida (ej. intentar prestar un dispositivo no disponible, o devolver un préstamo que ya fue devuelto).
- **422 Unprocessable Entity:** Error arrojado por Pydantic al fallar las validaciones de esquema (ej. `name` con menos de 3 caracteres, contraseña débil, `device_type` fuera del enum permitido).
- **429 Too Many Requests:** Se superó el límite de peticiones (rate limiting) configurado para el endpoint.

## Explicación breve del uso de Depends()

En esta API, `Depends()` se utiliza para implementar la **Inyección de Dependencias (Dependency Injection)**. La dependencia `get_db()` (en `app/dependencies/database_dependency.py`) abre una **sesión real de SQLAlchemy** (`SessionLocal`) al inicio de cada petición y la cierra automáticamente al finalizar (patrón `yield` + `finally`), inyectándola directamente en las funciones de las rutas (`path operations`). Esto centraliza el acceso a datos, evita fugas de conexiones y simplifica las pruebas, ya que `get_db` puede sobreescribirse fácilmente por una base de datos de prueba mediante `app.dependency_overrides`.

## Capa de servicios (`app/services/user_service.py`)

Toda la lógica de acceso a datos (crear, buscar por ID o email, listar con
filtros y orden, actualizar, actualizar parcialmente y eliminar) vive en la
capa de servicios, separada de las rutas. Esto mantiene `user_routes.py`
enfocado únicamente en: recibir la petición HTTP, validar reglas de negocio
(correo duplicado, cuerpo vacío) y traducir el resultado a códigos de estado
HTTP, delegando toda interacción con la base de datos a `user_service`.

## Explicación del manejo de errores implementado

El manejo de errores se gestiona utilizando la clase `HTTPException` de FastAPI. Esto permite interceptar flujos incorrectos y devolver respuestas HTTP claras.
- **Validaciones de negocio (400):** Se valida de forma manual que no se puedan crear o actualizar usuarios/dispositivos con un correo o número de serie que ya pertenezca a otro registro, ni registrar dos veces el mismo correo en `/auth/register`. También se controla que no se envíen peticiones PATCH vacías.
- **Autenticación (401):** `get_current_user` responde `401 Unauthorized` si no se envía token, el token es inválido/expiró, o el usuario del token ya no existe. `POST /auth/login` también responde `401` si el correo o la contraseña son incorrectos.
- **Autorización (403):** `require_roles(...)` responde `403 Forbidden` cuando el usuario está autenticado correctamente pero su rol no tiene permiso para la operación solicitada (ej. un `user` intentando crear un dispositivo, reservado a `admin`/`support`).
- **Validación de existencia (404):** Antes de ejecutar operaciones `GET`, `PUT`, `PATCH` o `DELETE` sobre un ID específico (de usuario, dispositivo o préstamo), el sistema verifica que el registro exista; de lo contrario, detiene el proceso inmediatamente devolviendo un error de recurso no encontrado.
- **Reglas de negocio incumplidas (409):** Al crear un préstamo, se valida que el dispositivo esté disponible (`is_available = True`); si no lo está, se responde `409 Conflict`. Lo mismo ocurre si se intenta devolver un préstamo que ya tiene estado `returned`.
- **Validación de esquema (422):** Pydantic v2 rechaza automáticamente contraseñas débiles, correos con formato inválido, roles fuera del enum permitido, etc., mediante `Field()` y `field_validator`.
- **Rate limiting (429):** `slowapi` intercepta las peticiones que superan el límite configurado por endpoint y responde `429 Too Many Requests` antes de que la petición llegue a la lógica de negocio.

## Documentación Swagger/OpenAPI (`/docs`, `/redoc`)

Los endpoints están organizados en la documentación automática mediante cinco
`tags`: **Auth**, **Users**, **Devices**, **Loans** y **Security** (este
último expone `GET /security/policy`, un resumen no sensible de la
configuración de seguridad activa). Cada `path operation` incluye `summary`
y `response_description` (por ejemplo, en `POST /loans` y
`PATCH /loans/{loan_id}/return`) para explicar qué hace el endpoint y qué
representa cada código de respuesta, además de los `description` definidos
en los `Query()` de los filtros y en los campos de los schemas Pydantic.

Como la API usa `OAuth2PasswordBearer`, Swagger UI muestra automáticamente el
botón **Authorize** 🔓: al hacer login (o pegar un token ya obtenido), todas
las peticiones de prueba dentro de `/docs` incluyen el header
`Authorization: Bearer <token>` automáticamente, lo que permite probar las
rutas protegidas directamente desde el navegador.

## Capturas y evidencias

Esta actividad (EV11) exige documentar el proyecto con capturas reales. Se
recomienda incluir aquí, como imágenes dentro de `assets/`, evidencia de:

- [ ] Estructura del proyecto (árbol de carpetas `app/auth`, `app/middlewares`, etc.).
- [ ] Migración de Alembic aplicada (`alembic upgrade head` en consola).
- [ ] Registro de usuario exitoso (`POST /auth/register`, `201`).
- [ ] Login y token generado (`POST /auth/login`, `200` con `access_token`).
- [ ] Respuesta de `GET /auth/me`.
- [ ] Acceso a una ruta protegida sin token (`401`).
- [ ] Acceso con un rol no permitido (`403`), por ejemplo un `user` en `POST /devices`.
- [ ] Swagger/OpenAPI con el botón **Authorize** y el esquema `OAuth2PasswordBearer`.
- [ ] Cabeceras del middleware (`X-App-Name`, `X-Process-Time`, `X-Request-ID`) en una respuesta.
- [ ] Prueba de rate limiting activado (`429 Too Many Requests`).

### Capturas heredadas (EV07)

Las siguientes capturas corresponden a la primera versión del proyecto (API
en memoria, sin base de datos ni seguridad) y se conservan como referencia
histórica:

![Vista General de Swagger](assets/swagger_general.png)
![Prueba Exitosa](assets/swagger_success.png)
![Manejo de Errores](assets/swagger_error.png)

## Reflexión sobre el uso de FastAPI, SQLAlchemy, Alembic y seguridad

FastAPI permite construir APIs REST de forma rápida y segura gracias a su
integración nativa con Pydantic para la validación de datos, la generación
automática de documentación interactiva (Swagger UI) y el manejo declarativo
de path/query parameters. En este proyecto se aplicaron modelos de entrada y
salida separados (`UserCreate` / `UserResponse`) para controlar exactamente
qué información se expone al cliente, además de cabeceras HTTP personalizadas
y manejo de errores mediante `HTTPException`.

Al incorporar **SQLAlchemy** como ORM, el proyecto pasó de almacenar los datos
en una lista en memoria (que se perdía al reiniciar el servidor) a persistirlos
en una base de datos SQLite real. Esto exigió separar claramente el **modelo
de base de datos** (`User`, `Device`, `Loan`, con sus columnas y constraints)
de los **schemas de la API** (Pydantic), y trasladar la lógica de consultas a
una capa de servicios independiente. El resultado es una aplicación más cercana
a un escenario productivo: los datos sobreviven a un reinicio del servidor, el
email y el número de serie se garantizan únicos a nivel de base de datos
(`unique=True`) y no solo por validación manual, y la sesión de base de datos
se gestiona de forma segura en cada petición gracias a `Depends(get_db)`.

Finalmente, incorporar **Alembic** resolvió un problema real de `create_all()`:
este último solo crea tablas que no existen, pero no sabe modificar una tabla
ya existente cuando cambia un modelo. Alembic versiona cada cambio de esquema
como una migración explícita (`alembic revision --autogenerate`), lo que
permite aplicar (`upgrade head`) o revertir (`downgrade -1`) cambios de forma
controlada y reproducible en cualquier entorno. Sumado a esto, modelar las
**asociaciones** entre `User`, `Device` y `Loan` con `relationship()` y
`ForeignKey()` permitió expresar reglas de negocio reales (un dispositivo no
puede prestarse dos veces mientras esté activo un préstamo) y construir
consultas con `join()` que devuelven, en una sola respuesta, información
combinada de varias tablas (`LoanDetailResponse`), algo mucho más parecido a
cómo se construyen APIs backend en un entorno profesional.

## Reflexión final sobre la importancia de la seguridad en APIs REST

Una API funcional no es una API segura, y esta actividad hizo evidente la
diferencia. Antes de EV11, cualquiera que conociera la URL de `device_systems`
podía crear, modificar o borrar usuarios y dispositivos sin restricción
alguna; el sistema no distinguía quién hacía la petición ni con qué
intención. Incorporar **autenticación** (saber quién eres) y **autorización**
(saber qué puedes hacer) como capas separadas —primero validar el token,
luego validar el rol— refleja cómo se diseña el control de acceso en
sistemas reales: nunca se confía en el cliente, siempre se verifica en el
servidor.

El **hash de contraseñas** con bcrypt fue igual de importante: si la base de
datos se filtrara, un atacante no obtendría las contraseñas reales, solo
hashes computacionalmente costosos de revertir. Guardar contraseñas en texto
plano —algo tentador por simplicidad— es uno de los errores de seguridad más
comunes y más graves en aplicaciones reales.

El **rate limiting** enseñó que la disponibilidad también es seguridad: sin
límites, un endpoint como `/auth/login` es un blanco fácil para ataques de
fuerza bruta, y `/auth/register` podría usarse para saturar la base de datos
con cuentas falsas. Limitar peticiones por IP no reemplaza otras defensas,
pero reduce drásticamente el costo de estos ataques automatizados.

Finalmente, **CORS** y el **middleware de trazabilidad** mostraron que la
seguridad no es solo "bloquear accesos": también es controlar con qué
sistemas puede hablar la API (evitando que cualquier sitio web use las
credenciales de un usuario en su nombre) y poder **auditar** qué pasó, cuándo
y con qué resultado, gracias al `X-Request-ID` y al registro de cada
petición. En conjunto, estas capas no buscan hacer la API "inhackeable"
—ningún sistema lo es—, sino reducir la superficie de ataque, limitar el daño
si algo falla, y dejar evidencia para investigar cuando ocurre.
