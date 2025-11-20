# 🎯 Event Management API - Guía Completa

Sistema completo de gestión de eventos con autenticación, interacción social y estadísticas.

## 📋 Tabla de Contenidos

1. [Instalación](#instalación)
2. [Configuración Inicial](#configuración-inicial)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Endpoints Disponibles](#endpoints-disponibles)
5. [Testing](#testing)
6. [Datos de Prueba](#datos-de-prueba)

## 🚀 Instalación

### 1. Crear entorno virtual
```bash
python -m venv venv
```

### 2. Activar entorno virtual
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## ⚙️ Configuración Inicial

### 1. Configurar MySQL
Asegúrate de tener MySQL instalado y corriendo en tu sistema con las siguientes credenciales por defecto:
- Host: `localhost`
- User: `root`
- Password: `` (vacío)

Si tus credenciales son diferentes, edita el archivo `app/database/connection.py`.

### 2. Inicializar base de datos completa
Este comando creará:
- ✅ Base de datos `event_management`
- ✅ 6 tablas
- ✅ 27 procedimientos almacenados (CRUD completo)

```bash
python init_database.py
```

**Salida esperada:**
```
🚀 INICIALIZANDO BASE DE DATOS - EVENT MANAGEMENT
🗄️  Creando base de datos...
✅ Base de datos creada o ya existe
📊 Creando tablas...
✅ Tablas creadas exitosamente
⚙️  Creando procedimientos almacenados...
   ✅ Procedimiento 1/27 creado
   ...
✨ ¡INICIALIZACIÓN COMPLETADA EXITOSAMENTE!
```

### 3. Cargar datos de prueba (OPCIONAL)
```bash
python seed_database.py
```

Esto creará:
- 6 usuarios de prueba
- 8 eventos (5 próximos, 3 pasados)
- 14 asistencias
- 7 comentarios
- 7 comparticiones

### 4. Ejecutar la aplicación
```bash
uvicorn app.main:app --reload --host localhost --port 8000
```

**URLs importantes:**
- 🌐 API: `http://localhost:8000`
- 📚 Documentación interactiva: `http://localhost:8000/docs`
- 📖 Documentación alternativa: `http://localhost:8000/redoc`

## 📁 Estructura del Proyecto

```
event-management/
├── app/
│   ├── database/
│   │   ├── connection.py          # Configuración de base de datos
│   │   └── procedures.sql         # SQL de referencia
│   ├── models/
│   │   ├── user_models.py         # Modelos: User, UserCreate, UserUpdate
│   │   ├── event_models.py        # Modelos: Event, EventCreate, EventUpdate
│   │   └── social_models.py       # Modelos: Comment, Share
│   ├── routes/
│   │   ├── auth_routes.py         # CRUD Users + Auth
│   │   ├── event_routes.py        # CRUD Events + Attendance
│   │   ├── social_routes.py       # CRUD Comments + Shares
│   │   ├── stats_routes.py        # Estadísticas
│   │   └── oauth_routes.py        # OAuth Google/Facebook
│   ├── services/
│   │   └── oauth_service.py       # Servicio de OAuth
│   ├── utils/
│   │   └── security.py            # Hashing bcrypt
│   └── main.py                    # App FastAPI
├── config.py                      # Configuración
├── init_database.py               # ⭐ Script de inicialización COMPLETO
├── seed_database.py               # Script de datos de prueba
├── requirements.txt               # Dependencias
├── test_complete.http            # 55 tests HTTP
├── LICENSE                        # Licencia MIT
└── README.md                      # Esta guía
```

## 🌐 Endpoints Disponibles

### 👥 Usuarios (CRUD Completo) - `/auth`

| Método | Endpoint | Descripción | Procedimiento |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Crear usuario | `CreateUser` |
| POST | `/auth/login` | Login | `GetUserByUsername` |
| GET | `/auth/users` | Listar usuarios | `GetAllUsers` |
| GET | `/auth/users/{id}` | Obtener por ID | `GetUserById` |
| PUT | `/auth/users/{id}` | Actualizar | `UpdateUser` |
| DELETE | `/auth/users/{id}` | Eliminar (soft) | `DeleteUser` |

### 📅 Eventos (CRUD Completo) - `/events`

| Método | Endpoint | Descripción | Procedimiento |
|--------|----------|-------------|---------------|
| POST | `/events/` | Crear evento | `CreateEvent` |
| GET | `/events/upcoming` | Próximos | `GetUpcomingEvents` |
| GET | `/events/past` | Pasados | `GetPastEvents` |
| GET | `/events/{id}` | Obtener por ID | `GetEventById` |
| PUT | `/events/{id}` | Actualizar | `UpdateEvent` |
| DELETE | `/events/{id}` | Eliminar (soft) | `DeleteEvent` |
| POST | `/events/attend` | Registrar asistencia | `RegisterAttendance` |
| GET | `/events/{id}/attendees` | Ver asistentes | `GetEventAttendees` |

### 💬 Comentarios (CRUD Completo) - `/social`

| Método | Endpoint | Descripción | Procedimiento |
|--------|----------|-------------|---------------|
| POST | `/social/comments` | Crear | `CreateComment` |
| GET | `/social/comments/{id}` | Obtener por ID | `GetCommentById` |
| GET | `/social/events/{id}/comments` | Por evento | `GetEventComments` |
| GET | `/social/users/{id}/comments` | Por usuario | `GetCommentsByUser` |
| PUT | `/social/comments/{id}` | Actualizar | `UpdateComment` |
| DELETE | `/social/comments/{id}` | Eliminar | `DeleteComment` |

### 🔗 Comparticiones (CRUD Completo) - `/social`

| Método | Endpoint | Descripción | Procedimiento |
|--------|----------|-------------|---------------|
| POST | `/social/share` | Compartir | `LogEventShare` |
| GET | `/social/shares/{id}` | Obtener por ID | `GetEventShareById` |
| GET | `/social/events/{id}/shares` | Por evento | `GetEventShares` |
| GET | `/social/shares` | Todas | `GetAllEventShares` |
| DELETE | `/social/shares/{id}` | Eliminar | `DeleteEventShare` |

### 📊 Estadísticas - `/stats`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/stats/user/{id}` | Stats de usuario |
| GET | `/stats/event/{id}` | Stats de evento |

### 🔐 OAuth - `/oauth`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/oauth/google` | Login con Google |
| POST | `/oauth/facebook` | Login con Facebook |

## 🧪 Testing

### Opción 1: REST Client (VSCode) - RECOMENDADO

1. Instala la extensión **REST Client** en VSCode
2. Abre `test_complete.http`
3. Click en "Send Request" sobre cada test
4. Los tests están organizados en secciones

### Opción 2: Swagger UI

1. Inicia la API
2. Abre `http://localhost:8000/docs`
3. Prueba los endpoints interactivamente

### Opción 3: cURL

```bash
# Ejemplo 1: Crear usuario
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "password123",
    "role": "participant"
  }'

# Ejemplo 2: Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Ejemplo 3: Listar eventos
curl http://localhost:8000/events/upcoming
```

### 📋 Estructura de Tests (55 tests)

```
test_complete.http
├── 👥 Users CRUD (8 tests)
├── 📅 Events CRUD (8 tests)
├── 💬 Comments CRUD (8 tests)
├── 🔗 Shares CRUD (6 tests)
├── 📊 Statistics (2 tests)
├── 🔐 OAuth (3 tests)
├── 🔄 Flujos completos (6 tests)
├── ❌ Tests de errores (9 tests)
└── 🔍 Verificación seed (5 tests)
```

## 📊 Datos de Prueba (Seed)

### Usuarios Disponibles

| Username | Email | Password | Role | ID |
|----------|-------|----------|------|-----|
| admin | admin@eventmanager.com | admin123 | organizer | 1 |
| juanperez | juan.perez@example.com | password123 | participant | 2 |
| mariagarcia | maria.garcia@example.com | password123 | organizer | 3 |
| carloslopez | carlos.lopez@example.com | password123 | participant | 4 |
| anasilva | ana.silva@example.com | password123 | organizer | 5 |
| pedromartinez | pedro.martinez@example.com | password123 | participant | 6 |

### Test Rápido del Seed

```bash
# 1. Login como admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. Ver eventos próximos
curl http://localhost:8000/events/upcoming

# 3. Ver estadísticas del admin
curl http://localhost:8000/stats/user/1
```

## 🔧 Solución de Problemas

### ❌ Error: "Failed to connect to database"

**Solución:**
```bash
# 1. Verifica que MySQL esté corriendo
mysql --version

# 2. Prueba la conexión
mysql -u root -p

# 3. Si las credenciales son diferentes, edita:
# app/database/connection.py (líneas 10-13)
```

### ❌ Error: "Procedure does not exist"

**Solución:**
```bash
# Reinicializa la base de datos
python init_database.py
```

Esto eliminará y recreará todos los procedimientos.

### ❌ Error en tests: "404 Not Found"

**Solución:**
1. Verifica que la API esté corriendo
2. Confirma la URL: `http://localhost:8000`
3. Si usaste seed, verifica los IDs en la base de datos
4. Ajusta los IDs en los tests según corresponda

### ❌ Error: "Database event_management already exists"

**No es un error**, la base ya existe. `init_database.py` usa `CREATE IF NOT EXISTS`.

Para **resetear completamente**:
```sql
-- En MySQL Workbench o terminal
DROP DATABASE event_management;
```

Luego ejecuta nuevamente:
```bash
python init_database.py
```

## 🔑 Características Importantes

### Seguridad
- ✅ Contraseñas hasheadas con **bcrypt**
- ✅ OAuth con Google y Facebook
- ✅ Validación de datos con **Pydantic**
- ✅ Protección contra SQL injection (stored procedures)

### Base de Datos
- ✅ **27 Procedimientos almacenados**
- ✅ CRUD completo para todas las entidades
- ✅ Soft delete (no elimina datos físicamente)
- ✅ Foreign keys con CASCADE
- ✅ Constraints y validaciones

### API
- ✅ FastAPI con documentación automática
- ✅ Respuestas tipadas con Pydantic
- ✅ Manejo de errores consistente
- ✅ CORS configurado

## 📈 Próximos Pasos Sugeridos

1. **Autenticación JWT**
   - Implementar tokens de acceso
   - Refresh tokens
   - Middleware de autenticación

2. **Paginación**
   - Limitar resultados en listados
   - Parámetros `skip` y `limit`

3. **Filtros y Búsqueda**
   - Filtrar eventos por fecha/ubicación
   - Buscar usuarios por nombre
   - Full-text search

4. **Notificaciones**
   - Email al registrarse a evento
   - Recordatorios de eventos
   - Notificaciones de comentarios

5. **Imágenes**
   - Upload de fotos de perfil
   - Imágenes de eventos
   - Storage en cloud (AWS S3, Cloudinary)

6. **Rate Limiting**
   - Protección contra abuso
   - Límites por IP/usuario

7. **Tests Automatizados**
   - Pytest para unit tests
   - Tests de integración
   - CI/CD con GitHub Actions

## 📞 Soporte

¿Problemas? Revisa:
1. Los logs de la API
2. Los logs de MySQL
3. El archivo `test_complete.http` para ejemplos

## 📄 Licencia

MIT License - Ver archivo `LICENSE`

---

**✨ ¡Todo listo para desarrollar! 🚀**

**Comandos rápidos:**
```bash
# Setup inicial
python init_database.py
python seed_database.py

# Ejecutar
uvicorn app.main:app --reload

# Verificar
curl http://localhost:8000
```