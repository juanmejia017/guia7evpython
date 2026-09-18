# device_systems

API REST desarrollada con **FastAPI**, **SQLAlchemy** y **Alembic** para la
gestión de **usuarios**, **dispositivos** y **préstamos** dentro del sistema
`device_systems`, con persistencia real en base de datos, relaciones entre
modelos y migraciones versionadas.

Proyecto realizado para las actividades:
- **GA1-220501096-01-AA1-EV07 – Fundamentos de FastAPI: API REST para Gestión de Usuarios** (SENA, ADSO).
- **GA1-220501096-01-AA1-EV09 – FastAPI con SQLAlchemy: Persistencia de Datos y CRUD sobre Base de Datos** (SENA, ADSO).
- **GA1-220501096-01-AA1-EV10 – FastAPI Avanzado: Migraciones con Alembic, Asociaciones de Modelos y Consultas con Joins** (SENA, ADSO).

## Descripción de la aplicación

`device_systems` expone un API REST que permite:

- Gestionar usuarios (`/users`), dispositivos (`/devices`) y préstamos (`/loans`) con CRUD completo donde aplica.
- Listar usuarios, con filtros opcionales por `role` y `is_active`, y orden por `name` o `created_at` (`order_by`, `-order_by`).
- Listar dispositivos, con filtros por `device_type`, `is_available`, `brand` y búsqueda libre (`search`) usando `ilike()`.
- Registrar préstamos, validando que el usuario y el dispositivo existan y que el dispositivo esté disponible; al prestarlo, el dispositivo queda marcado como no disponible.
- Registrar la devolución de un préstamo (`PATCH /loans/{id}/return`), liberando el dispositivo automáticamente.
- Consultar préstamos con información relacionada de usuario y dispositivo mediante **joins** (`/loans`, `/loans/details`, `/users/{id}/loans`, `/devices/{id}/loans`), con filtros por `status`, `user_id`, `device_id`, `user_email` o `device_type`.
- Persistir todos los datos en una base de datos **SQLite** mediante el ORM **SQLAlchemy**, versionando los cambios de esquema con **Alembic**.
- Retornar respuestas estandarizadas mediante `response_model`, ocultando cualquier dato interno que no deba exponerse.
- Enviar cabeceras HTTP personalizadas en cada respuesta:
  - `X-App-Name: device_systems`
  - `X-API-Version: 3.0`

## Estructura del proyecto

```text
device_systems/
├── app/
│   ├── main.py
│   ├── database/
│   │   └── connection.py      # engine, SessionLocal y Base declarativa
│   ├── models/
│   │   ├── user_model.py      # modelo SQLAlchemy (tabla users)
│   │   ├── device_model.py    # modelo SQLAlchemy (tabla devices)
│   │   └── loan_model.py      # modelo SQLAlchemy (tabla loans, FKs a users/devices)
│   ├── schemas/
│   │   ├── user_schema.py     # schemas Pydantic de users
│   │   ├── device_schema.py   # schemas Pydantic de devices
│   │   └── loan_schema.py     # schemas Pydantic de loans (incluye LoanDetailResponse)
│   ├── routes/
│   │   ├── user_routes.py     # endpoints de /users (incluye /users/{id}/loans)
│   │   ├── device_routes.py   # endpoints de /devices (incluye /devices/{id}/loans)
│   │   └── loan_routes.py     # endpoints de /loans (creación, devolución, joins)
│   ├── services/
│   │   ├── user_service.py    # lógica de acceso a datos de users
│   │   ├── device_service.py  # lógica de acceso a datos de devices
│   │   └── loan_service.py    # lógica de negocio y consultas con joins de loans
│   └── dependencies/
│       └── database_dependency.py  # get_db(): sesión de base de datos por request
├── alembic/
│   ├── env.py                 # configuración de Alembic (URL y metadata de los modelos)
│   └── versions/               # historial de migraciones generadas
├── alembic.ini
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
- **201 Created:** Registro creado de forma exitosa (POST de usuarios, dispositivos o préstamos).
- **204 No Content:** Usuario o dispositivo eliminado correctamente (DELETE).
- **400 Bad Request:** Error del cliente (ej. correo o número de serie duplicado, envío de datos inválidos o PATCH vacío).
- **404 Not Found:** Recurso no encontrado (ej. usuario, dispositivo o préstamo inexistente).
- **409 Conflict:** Regla de negocio incumplida (ej. intentar prestar un dispositivo no disponible, o devolver un préstamo que ya fue devuelto).
- **422 Unprocessable Entity:** Error arrojado por Pydantic al fallar las validaciones de esquema (ej. `name` con menos de 3 caracteres, `device_type` fuera del enum permitido).

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
- **Validaciones de negocio (400):** Se valida de forma manual que no se puedan crear o actualizar usuarios/dispositivos con un correo o número de serie que ya pertenezca a otro registro. También se controla que no se envíen peticiones PATCH vacías.
- **Validación de existencia (404):** Antes de ejecutar operaciones `GET`, `PUT`, `PATCH` o `DELETE` sobre un ID específico (de usuario, dispositivo o préstamo), el sistema verifica que el registro exista; de lo contrario, detiene el proceso inmediatamente devolviendo un error de recurso no encontrado.
- **Reglas de negocio incumplidas (409):** Al crear un préstamo, se valida que el dispositivo esté disponible (`is_available = True`); si no lo está, se responde `409 Conflict`. Lo mismo ocurre si se intenta devolver un préstamo que ya tiene estado `returned`.

## Documentación Swagger/OpenAPI (`/docs`, `/redoc`)

Los endpoints están organizados en la documentación automática mediante tres
`tags`: **Users**, **Devices** y **Loans**. Cada `path operation` incluye
`summary` y `response_description` (por ejemplo, en `POST /loans` y
`PATCH /loans/{loan_id}/return`) para explicar qué hace el endpoint y qué
representa cada código de respuesta, además de los `description` definidos
en los `Query()` de los filtros (`device_type`, `is_available`, `search`,
`status`, `user_email`, etc.) y en los campos de los schemas Pydantic.

## Capturas de Swagger UI

## 📸 Evidencias de Ejecución y Pruebas (Swagger UI)

A continuación se muestran las capturas de pantalla que validan el correcto funcionamiento de la API (`device_systems`), abarcando la vista general, respuestas exitosas y el manejo de errores:

### 1. Vista General de la API
![Vista General de Swagger](assets/swagger_general.png)

### 2. Respuesta Exitosa (Creación de Usuario - 201 Created)
![Prueba Exitosa](assets/swagger_success.png)

### 3. Manejo de Errores (Correo Duplicado - 400 Bad Request)
![Manejo de Errores](assets/swagger_error.png)

> Las capturas anteriores corresponden a la versión en memoria (EV07). Se
> recomienda regenerarlas contra la versión actual (EV10), con los tres
> tags **Users**, **Devices** y **Loans** visibles en `/docs`.

## Reflexión sobre el uso de FastAPI, SQLAlchemy y Alembic

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
