# device_systems

API REST desarrollada con **FastAPI** y **SQLAlchemy** para la gestión del
recurso **usuarios** dentro del sistema `device_systems`, con persistencia
real en base de datos.

Proyecto realizado para las actividades:
- **GA1-220501096-01-AA1-EV07 – Fundamentos de FastAPI: API REST para Gestión de Usuarios** (SENA, ADSO).
- **GA1-220501096-01-AA1-EV09 – FastAPI con SQLAlchemy: Persistencia de Datos y CRUD sobre Base de Datos** (SENA, ADSO).

## Descripción de la aplicación

`device_systems` expone un API REST que permite:

- Listar usuarios, con filtros opcionales por `role` y `is_active`, y orden por `name` o `created_at` (`order_by`, `-order_by`).
- Consultar un usuario puntual mediante su `id` (path parameter).
- Registrar nuevos usuarios (POST), validando los datos con **Pydantic v2** y evitando correos duplicados.
- Actualizar de forma completa (PUT) o parcial (PATCH) los datos de un usuario existente.
- Eliminar usuarios del sistema (DELETE).
- Persistir todos los datos en una base de datos **SQLite** mediante el ORM **SQLAlchemy**, en lugar de estructuras en memoria.
- Retornar respuestas estandarizadas mediante `response_model`, ocultando cualquier dato interno que no deba exponerse.
- Enviar cabeceras HTTP personalizadas en cada respuesta:
  - `X-App-Name: device_systems`
  - `X-API-Version: 2.0`

## Estructura del proyecto

```text
device_systems/
├── app/
│   ├── main.py
│   ├── database/
│   │   └── connection.py      # engine, SessionLocal y Base declarativa
│   ├── models/
│   │   └── user_model.py      # modelo SQLAlchemy (tabla users)
│   ├── schemas/
│   │   └── user_schema.py     # schemas Pydantic (entrada/salida de la API)
│   ├── routes/
│   │   └── user_routes.py     # endpoints HTTP del recurso users
│   ├── services/
│   │   └── user_service.py    # lógica de acceso a datos (CRUD, filtros, orden)
│   └── dependencies/
│       └── database_dependency.py  # get_db(): sesión de base de datos por request
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

Al iniciar, la aplicación crea automáticamente el archivo `device_systems.db`
(SQLite) y la tabla `users`, si todavía no existen (`Base.metadata.create_all`
en `app/main.py`), por lo que no se requiere ningún paso manual de migración
para levantar el proyecto por primera vez.

La API quedará disponible en `http://127.0.0.1:8000` y la documentación interactiva (Swagger UI) en `http://127.0.0.1:8000/docs`.

## Tabla de endpoints

| Método | Endpoint               | Descripción                                     |
|--------|------------------------|-------------------------------------------------|
| GET    | `/`                    | Verifica el estado del servicio                 |
| GET    | `/users`               | Lista todos los usuarios                        |
| GET    | `/users?role=admin`    | Filtra usuarios por rol                         |
| GET    | `/users?is_active=true`| Filtra usuarios por estado activo/inactivo      |
| GET    | `/users?order_by=-name`| Ordena por `name`, `-name`, `created_at` o `-created_at` |
| GET    | `/users/{user_id}`     | Consulta un usuario por su ID                   |
| POST   | `/users`               | Registra un nuevo usuario                       |
| PUT    | `/users/{user_id}`     | Actualiza completamente un usuario existente    |
| PATCH  | `/users/{user_id}`     | Actualiza parcialmente los datos de un usuario  |
| DELETE | `/users/{user_id}`     | Elimina un usuario del sistema                  |

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

## Códigos de estado usados

- **200 OK:** Petición procesada correctamente (GET, PUT, PATCH).
- **201 Created:** Usuario creado de forma exitosa (POST).
- **204 No Content:** Usuario eliminado correctamente (DELETE).
- **400 Bad Request:** Error del cliente (ej. correo duplicado, envío de datos inválidos o PATCH vacío).
- **404 Not Found:** Recurso no encontrado (ej. intentar consultar, actualizar o eliminar un ID inexistente).
- **422 Unprocessable Entity:** Error arrojado por Pydantic al fallar las validaciones de esquema (ej. `name` con menos de 3 caracteres).

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
- **Validaciones de negocio (400):** Se valida de forma manual que no se puedan crear o actualizar usuarios con un correo electrónico que ya pertenezca a otra cuenta. También se controla que no se envíen peticiones PATCH vacías.
- **Validación de existencia (404):** Antes de ejecutar operaciones `GET`, `PUT`, `PATCH` o `DELETE` sobre un ID específico, el sistema verifica que el registro exista; de lo contrario, detiene el proceso inmediatamente devolviendo un error de recurso no encontrado.

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
> recomienda regenerarlas contra la versión con persistencia en base de datos
> (EV09) para reflejar el campo `created_at` en las respuestas.

## Reflexión sobre el uso de FastAPI y SQLAlchemy

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
de base de datos** (`User` en `app/models/user_model.py`, con sus columnas y
constraints) de los **schemas de la API** (Pydantic), y trasladar la lógica de
consultas a una capa de servicios independiente. El resultado es una
aplicación más cercana a un escenario productivo: los datos sobreviven a un
reinicio del servidor, el email se garantiza único a nivel de base de datos
(`unique=True`) y no solo por validación manual, y la sesión de base de datos
se gestiona de forma segura en cada petición gracias a `Depends(get_db)`.
