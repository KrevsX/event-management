import mysql.connector
from mysql.connector import Error


def init_database():
    connection = None
    try:
        # Conectar a MySQL sin especificar base de datos
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )

        cursor = connection.cursor()

        # ============================================
        # 1. CREAR BASE DE DATOS
        # ============================================
        print("🗄️  Creando base de datos...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS event_management")
        cursor.execute("USE event_management")
        print("✅ Base de datos creada o ya existe")

        # ============================================
        # 2. CREAR TABLAS
        # ============================================
        print("\n📊 Creando tablas...")

        tables_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('organizer', 'participant') DEFAULT 'participant',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );

        CREATE TABLE IF NOT EXISTS social_auth (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            provider VARCHAR(50) NOT NULL,
            provider_id VARCHAR(100) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_provider (provider, provider_id)
        );

        CREATE TABLE IF NOT EXISTS events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            date DATETIME NOT NULL,
            location VARCHAR(200) NOT NULL,
            max_participants INT,
            organizer_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (organizer_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS event_attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            event_id INT NOT NULL,
            attended BOOLEAN DEFAULT FALSE,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id),
            UNIQUE KEY unique_attendance (user_id, event_id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            event_id INT NOT NULL,
            content TEXT NOT NULL,
            rating INT CHECK (rating >= 1 AND rating <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        );

        CREATE TABLE IF NOT EXISTS event_shares (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_id INT NOT NULL,
            share_type ENUM('social_media', 'email') NOT NULL,
            recipient VARCHAR(255),
            shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(id)
        );
        """

        # Ejecutar creación de tablas
        for statement in tables_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)

        print("✅ Tablas creadas exitosamente")

        # ============================================
        # 3. CREAR STORED PROCEDURES
        # ============================================
        print("\n⚙️  Creando procedimientos almacenados...")

        # Primero, eliminar procedimientos existentes si existen
        print("   Limpiando procedimientos antiguos...")
        drop_procedures = [
            "DROP PROCEDURE IF EXISTS CreateUser",
            "DROP PROCEDURE IF EXISTS GetUserByUsername",
            "DROP PROCEDURE IF EXISTS GetUserById",
            "DROP PROCEDURE IF EXISTS UpdateUser",
            "DROP PROCEDURE IF EXISTS DeleteUser",
            "DROP PROCEDURE IF EXISTS GetAllUsers",
            "DROP PROCEDURE IF EXISTS CreateEvent",
            "DROP PROCEDURE IF EXISTS GetEventById",
            "DROP PROCEDURE IF EXISTS GetUpcomingEvents",
            "DROP PROCEDURE IF EXISTS GetPastEvents",
            "DROP PROCEDURE IF EXISTS UpdateEvent",
            "DROP PROCEDURE IF EXISTS DeleteEvent",
            "DROP PROCEDURE IF EXISTS RegisterAttendance",
            "DROP PROCEDURE IF EXISTS GetEventAttendees",
            "DROP PROCEDURE IF EXISTS CreateComment",
            "DROP PROCEDURE IF EXISTS GetCommentById",
            "DROP PROCEDURE IF EXISTS GetEventComments",
            "DROP PROCEDURE IF EXISTS GetCommentsByUser",
            "DROP PROCEDURE IF EXISTS UpdateComment",
            "DROP PROCEDURE IF EXISTS DeleteComment",
            "DROP PROCEDURE IF EXISTS LogEventShare",
            "DROP PROCEDURE IF EXISTS GetEventShareById",
            "DROP PROCEDURE IF EXISTS GetEventShares",
            "DROP PROCEDURE IF EXISTS GetAllEventShares",
            "DROP PROCEDURE IF EXISTS DeleteEventShare",
            "DROP PROCEDURE IF EXISTS GetUserEventStats",
            "DROP PROCEDURE IF EXISTS GetEventStatistics"
        ]

        for drop_proc in drop_procedures:
            try:
                cursor.execute(drop_proc)
            except:
                pass

        # Lista de todos los procedimientos almacenados
        procedures = [
            # ==========================================
            # PROCEDIMIENTOS DE USUARIOS (CRUD COMPLETO)
            # ==========================================
            """
            CREATE PROCEDURE CreateUser(
                IN p_username VARCHAR(50),
                IN p_email VARCHAR(100),
                IN p_full_name VARCHAR(100),
                IN p_password_hash VARCHAR(255),
                IN p_role VARCHAR(20)
            )
            BEGIN
                INSERT INTO users (username, email, full_name, password_hash, role)
                VALUES (p_username, p_email, p_full_name, p_password_hash, p_role);
                SELECT LAST_INSERT_ID() as user_id;
            END
            """,

            """
            CREATE PROCEDURE GetUserByUsername(IN p_username VARCHAR(50))
            BEGIN
                SELECT id, username, email, full_name, password_hash, role, created_at
                FROM users
                WHERE username = p_username AND is_active = TRUE;
            END
            """,

            """
            CREATE PROCEDURE GetUserById(IN p_user_id INT)
            BEGIN
                SELECT id, username, email, full_name, role, created_at
                FROM users
                WHERE id = p_user_id AND is_active = TRUE;
            END
            """,

            """
            CREATE PROCEDURE UpdateUser(
                IN p_user_id INT,
                IN p_username VARCHAR(50),
                IN p_email VARCHAR(100),
                IN p_full_name VARCHAR(100),
                IN p_password_hash VARCHAR(255),
                IN p_role VARCHAR(20)
            )
            BEGIN
                UPDATE users
                SET username = COALESCE(p_username, username),
                    email = COALESCE(p_email, email),
                    full_name = COALESCE(p_full_name, full_name),
                    password_hash = COALESCE(p_password_hash, password_hash),
                    role = COALESCE(p_role, role)
                WHERE id = p_user_id;
            END
            """,

            """
            CREATE PROCEDURE DeleteUser(IN p_user_id INT)
            BEGIN
                UPDATE users SET is_active = FALSE WHERE id = p_user_id;
            END
            """,

            """
            CREATE PROCEDURE GetAllUsers()
            BEGIN
                SELECT id, username, email, full_name, role, created_at
                FROM users
                WHERE is_active = TRUE
                ORDER BY created_at DESC;
            END
            """,

            # ==========================================
            # PROCEDIMIENTOS DE EVENTOS (CRUD COMPLETO)
            # ==========================================
            """
            CREATE PROCEDURE CreateEvent(
                IN p_title VARCHAR(200),
                IN p_description TEXT,
                IN p_date DATETIME,
                IN p_location VARCHAR(200),
                IN p_max_participants INT,
                IN p_organizer_id INT
            )
            BEGIN
                INSERT INTO events (title, description, date, location, max_participants, organizer_id)
                VALUES (p_title, p_description, p_date, p_location, p_max_participants, p_organizer_id);
                SELECT LAST_INSERT_ID() as event_id;
            END
            """,

            """
            CREATE PROCEDURE GetEventById(IN p_event_id INT)
            BEGIN
                SELECT e.*, u.username as organizer_name, u.full_name as organizer_full_name
                FROM events e
                JOIN users u ON e.organizer_id = u.id
                WHERE e.id = p_event_id AND e.is_active = TRUE;
            END
            """,

            """
            CREATE PROCEDURE GetUpcomingEvents()
            BEGIN
                SELECT e.*, u.username as organizer_name, u.full_name as organizer_full_name
                FROM events e
                JOIN users u ON e.organizer_id = u.id
                WHERE e.date >= NOW() AND e.is_active = TRUE
                ORDER BY e.date ASC;
            END
            """,

            """
            CREATE PROCEDURE GetPastEvents()
            BEGIN
                SELECT e.*, u.username as organizer_name, u.full_name as organizer_full_name
                FROM events e
                JOIN users u ON e.organizer_id = u.id
                WHERE e.date < NOW() AND e.is_active = TRUE
                ORDER BY e.date DESC;
            END
            """,

            """
            CREATE PROCEDURE UpdateEvent(
                IN p_event_id INT,
                IN p_title VARCHAR(200),
                IN p_description TEXT,
                IN p_date DATETIME,
                IN p_location VARCHAR(200),
                IN p_max_participants INT
            )
            BEGIN
                UPDATE events
                SET title = COALESCE(p_title, title),
                    description = COALESCE(p_description, description),
                    date = COALESCE(p_date, date),
                    location = COALESCE(p_location, location),
                    max_participants = COALESCE(p_max_participants, max_participants)
                WHERE id = p_event_id;
            END
            """,

            """
            CREATE PROCEDURE DeleteEvent(IN p_event_id INT)
            BEGIN
                UPDATE events SET is_active = FALSE WHERE id = p_event_id;
            END
            """,

            # ==========================================
            # PROCEDIMIENTOS DE ASISTENCIA
            # ==========================================
            """
            CREATE PROCEDURE RegisterAttendance(
                IN p_user_id INT,
                IN p_event_id INT
            )
            BEGIN
                INSERT INTO event_attendance (user_id, event_id)
                VALUES (p_user_id, p_event_id)
                ON DUPLICATE KEY UPDATE attended = TRUE;
            END
            """,

            """
            CREATE PROCEDURE GetEventAttendees(IN p_event_id INT)
            BEGIN
                SELECT u.id, u.username, u.full_name, ea.registered_at, ea.attended
                FROM event_attendance ea
                JOIN users u ON ea.user_id = u.id
                WHERE ea.event_id = p_event_id;
            END
            """,

            # ==========================================
            # PROCEDIMIENTOS DE COMENTARIOS (CRUD COMPLETO)
            # ==========================================
            """
            CREATE PROCEDURE CreateComment(
                IN p_user_id INT,
                IN p_event_id INT,
                IN p_content TEXT,
                IN p_rating INT
            )
            BEGIN
                INSERT INTO comments (user_id, event_id, content, rating)
                VALUES (p_user_id, p_event_id, p_content, p_rating);
                SELECT LAST_INSERT_ID() as comment_id;
            END
            """,

            """
            CREATE PROCEDURE GetCommentById(IN p_comment_id INT)
            BEGIN
                SELECT c.*, u.username, u.full_name
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.id = p_comment_id;
            END
            """,

            """
            CREATE PROCEDURE GetEventComments(IN p_event_id INT)
            BEGIN
                SELECT c.*, u.username, u.full_name
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.event_id = p_event_id
                ORDER BY c.created_at DESC;
            END
            """,

            """
            CREATE PROCEDURE GetCommentsByUser(IN p_user_id INT)
            BEGIN
                SELECT c.*, e.title as event_title
                FROM comments c
                JOIN events e ON c.event_id = e.id
                WHERE c.user_id = p_user_id
                ORDER BY c.created_at DESC;
            END
            """,

            """
            CREATE PROCEDURE UpdateComment(
                IN p_comment_id INT,
                IN p_content TEXT,
                IN p_rating INT
            )
            BEGIN
                UPDATE comments
                SET content = COALESCE(p_content, content),
                    rating = COALESCE(p_rating, rating)
                WHERE id = p_comment_id;
            END
            """,

            """
            CREATE PROCEDURE DeleteComment(IN p_comment_id INT)
            BEGIN
                DELETE FROM comments WHERE id = p_comment_id;
            END
            """,

            # ==========================================
            # PROCEDIMIENTOS DE COMPARTICIONES (CRUD COMPLETO)
            # ==========================================
            """
            CREATE PROCEDURE LogEventShare(
                IN p_event_id INT,
                IN p_share_type VARCHAR(20),
                IN p_recipient VARCHAR(255)
            )
            BEGIN
                INSERT INTO event_shares (event_id, share_type, recipient)
                VALUES (p_event_id, p_share_type, p_recipient);
            END
            """,

            """
            CREATE PROCEDURE GetEventShareById(IN p_share_id INT)
            BEGIN
                SELECT * FROM event_shares WHERE id = p_share_id;
            END
            """,

            """
            CREATE PROCEDURE GetEventShares(IN p_event_id INT)
            BEGIN
                SELECT * FROM event_shares 
                WHERE event_id = p_event_id
                ORDER BY shared_at DESC;
            END
            """,

            """
            CREATE PROCEDURE GetAllEventShares()
            BEGIN
                SELECT es.*, e.title as event_title
                FROM event_shares es
                JOIN events e ON es.event_id = e.id
                ORDER BY es.shared_at DESC;
            END
            """,

            """
            CREATE PROCEDURE DeleteEventShare(IN p_share_id INT)
            BEGIN
                DELETE FROM event_shares WHERE id = p_share_id;
            END
            """,

            # ==========================================
            # PROCEDIMIENTOS DE ESTADÍSTICAS
            # ==========================================
            """
            CREATE PROCEDURE GetUserEventStats(IN p_user_id INT)
            BEGIN
                SELECT
                    (SELECT COUNT(*) FROM event_attendance WHERE user_id = p_user_id) as events_registered,
                    (SELECT COUNT(*) FROM event_attendance WHERE user_id = p_user_id AND attended = TRUE) as events_attended,
                    (SELECT COUNT(*) FROM events WHERE organizer_id = p_user_id) as events_organized;
            END
            """,

            """
            CREATE PROCEDURE GetEventStatistics(IN p_event_id INT)
            BEGIN
                SELECT
                    e.title,
                    e.date,
                    e.location,
                    (SELECT COUNT(*) FROM event_attendance WHERE event_id = p_event_id) as total_registered,
                    (SELECT COUNT(*) FROM event_attendance WHERE event_id = p_event_id AND attended = TRUE) as total_attended,
                    (SELECT AVG(rating) FROM comments WHERE event_id = p_event_id) as average_rating,
                    (SELECT COUNT(*) FROM comments WHERE event_id = p_event_id) as total_comments,
                    (SELECT COUNT(*) FROM event_shares WHERE event_id = p_event_id) as total_shares
                FROM events e
                WHERE e.id = p_event_id;
            END
            """
        ]

        # Ejecutar cada procedimiento individualmente
        for i, procedure in enumerate(procedures, 1):
            try:
                cursor.execute(procedure)
                print(f"   ✅ Procedimiento {i}/{len(procedures)} creado")
            except Error as e:
                print(f"   ⚠️  Error en procedimiento {i}: {e}")
                continue

        connection.commit()

        # ============================================
        # 4. RESUMEN FINAL
        # ============================================
        print("\n" + "=" * 60)
        print("✨ ¡INICIALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("=" * 60)

        print("\n📊 Resumen de la base de datos:")
        print("   ✅ Base de datos: event_management")
        print("   ✅ Tablas creadas: 6")
        print("     - users")
        print("     - social_auth")
        print("     - events")
        print("     - event_attendance")
        print("     - comments")
        print("     - event_shares")

        print(f"\n   ✅ Procedimientos almacenados: {len(procedures)}")
        print("\n   📋 CRUD Completo para:")
        print("     - Usuarios (6 procedimientos)")
        print("     - Eventos (6 procedimientos)")
        print("     - Comentarios (6 procedimientos)")
        print("     - Comparticiones (5 procedimientos)")
        print("     - Asistencias (2 procedimientos)")
        print("     - Estadísticas (2 procedimientos)")

        print("\n🚀 Próximos pasos:")
        print("   1. Ejecutar: python seed_database.py (opcional - datos de prueba)")
        print("   2. Ejecutar: uvicorn app.main:app --reload")
        print("   3. Abrir: http://localhost:8000/docs")
        print("\n" + "=" * 60)

    except Error as e:
        print(f"\n❌ Error durante la inicialización: {e}")
        print("\n💡 Sugerencias:")
        print("   - Verifica que MySQL esté corriendo")
        print("   - Confirma las credenciales de conexión")
        print("   - Asegúrate de tener permisos para crear bases de datos")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔌 Conexión cerrada correctamente")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 INICIALIZANDO BASE DE DATOS - EVENT MANAGEMENT")
    print("=" * 60)
    init_database()