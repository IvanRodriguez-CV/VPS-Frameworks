# API REST del sistema bibliotecario

API REST con FastAPI y SQLModel para administrar usuarios, roles, autores,
categorías, libros, ejemplares y préstamos. La implementación sigue la
organización por modelos, routers y dependencias trabajada en las guías y usa
MySQL para la persistencia.

## Requisitos

- Python 3.10 o posterior.
- MySQL debe estar iniciado y la base de datos `biblioteca` debe existir antes
  de ejecutar la API. Las tablas se crean al iniciar la aplicación.

## Preparación en Windows

Desde esta carpeta, abre una terminal y ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` y configura al menos:

- `DATABASE_URL`: ajusta el usuario, contraseña, host, puerto y nombre de la
  base de datos MySQL.
- `SECRET_KEY_TOKEN`: clave privada para firmar los tokens; reemplaza el valor
  vacío por una clave propia y no compartas el archivo `.env`.
- `INITIAL_ADMIN_USERNAME` y `INITIAL_ADMIN_PASSWORD`: credenciales para crear
  el primer administrador. Usa una contraseña de al menos 8 caracteres.

El primer inicio crea las tablas y los roles `admin`, `librarian` y `user`. Si
se configuran las dos variables del administrador inicial, también crea ese
usuario si todavía no existe. El registro público siempre asigna el rol `user`.

## Ejecutar y probar

```powershell
fastapi dev main.py
```

La documentación interactiva se encuentra en `http://127.0.0.1:8000/docs` y
la documentación ReDoc en `http://127.0.0.1:8000/redoc`.

Para ejecutar las pruebas:

```powershell
pytest -q
```

Las pruebas usan una base SQLite en memoria y no necesitan conectarse a MySQL.

## Rutas principales

Las rutas de negocio requieren `Authorization: Bearer <token>`, salvo el
registro y el login.

| Método | Ruta | Acceso | Función |
|---|---|---|---|
| POST | `/auth/register` | Público | Registrar un usuario con rol `user` |
| POST | `/auth/login` | Público | Validar credenciales y emitir token |
| GET | `/auth/me` | Autenticado | Consultar la cuenta autenticada |
| GET, POST | `/users/` | Administrador | Consultar y crear usuarios |
| GET, PATCH, DELETE | `/users/{user_id}` | Autenticado/administrador | Consultar, actualizar o eliminar usuarios |
| CRUD | `/roles/` y `/roles/{role_id}` | Administrador | Administrar roles |
| CRUD | `/authors/` y `/authors/{author_id}` | Administrador/bibliotecario | Administrar autores |
| CRUD | `/categories/` y `/categories/{category_id}` | Administrador/bibliotecario | Administrar categorías |
| CRUD | `/books/` y `/books/{book_id}` | Administrador/bibliotecario | Administrar libros |
| GET, POST | `/books/{book_id}/copies` | Autenticado/administrador/bibliotecario | Consultar y agregar ejemplares |
| DELETE | `/copies/{copy_id}` | Administrador/bibliotecario | Eliminar ejemplares sin historial |
| GET, POST | `/loans/` | Autenticado | Consultar préstamos permitidos y crear un préstamo propio |
| GET | `/loans/{loan_id}` | Propietario/administrador/bibliotecario | Consultar un préstamo |
| POST | `/loans/{loan_id}/return` | Propietario/administrador/bibliotecario | Registrar una devolución |

El login usa el formulario OAuth2 `username`/`password`. El token firmado con
PyJWT expira según `ACCESS_TOKEN_EXPIRE_MINUTES` (30 minutos por defecto).
Las contraseñas se almacenan como hashes bcrypt. Las contraseñas y claves no
se incluyen en las respuestas.

## Flujo de demostración

1. Inicia sesión en `/auth/login` con el usuario administrador inicial y copia
   `access_token`.
2. Autoriza la documentación de `/docs` con el token Bearer.
3. Crea un autor y una categoría; crea un libro indicando sus identificadores.
   La creación del libro genera un ejemplar disponible por defecto. Se puede
   solicitar más de uno con `copies_count`.
4. Registra un usuario desde `/auth/register` y vuelve a iniciar sesión con
   ese usuario.
5. Consulta el libro y sus ejemplares; crea un préstamo enviando `copy_id` y
   `due_date` futura en formato ISO 8601 con zona horaria, por ejemplo
   `2027-01-15T17:00:00-06:00`.
6. Repite el préstamo del mismo ejemplar para comprobar el rechazo por
   indisponibilidad. Devuelve el préstamo con `/loans/{loan_id}/return` y
   consulta el ejemplar para verificar que volvió a estar disponible.

Las respuestas usan códigos HTTP como 201 para creación, 204 para eliminación,
401 para credenciales/token inválidos, 403 para permisos insuficientes, 404
para recursos inexistentes y 409 para conflictos de disponibilidad o
integridad. No se eliminan libros, categorías, autores, usuarios o ejemplares
que tengan relaciones que deban conservarse.

## Material utilizado

La estructura y los conceptos implementados se basan en las guías PDF 1–9 y en
la rúbrica `Proyecto_API_Sistema_Bibliotecario_Rubrica_Competencias.pdf`
compartidas para este proyecto.
