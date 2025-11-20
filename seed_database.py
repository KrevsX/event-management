import mysql.connector
from mysql.connector import Error
from app.utils.security import hash_password
from datetime import datetime, timedelta


def seed_database():
    connection = None
    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="event_management"
        )

        cursor = connection.cursor(dictionary=True)
        print("🌱 Iniciando seed de la base de datos...")

        # ============== 1. USUARIOS ==============
        print("\n👥 Creando usuarios...")

        users_data = [
            ("admin", "admin@eventmanager.com", "Administrador Sistema", hash_password("admin123"), "organizer"),
            ("juanperez", "juan.perez@example.com", "Juan Pérez", hash_password("password123"), "participant"),
            ("mariagarcia", "maria.garcia@example.com", "María García", hash_password("password123"), "organizer"),
            ("carloslopez", "carlos.lopez@example.com", "Carlos López", hash_password("password123"), "participant"),
            ("anasilva", "ana.silva@example.com", "Ana Silva", hash_password("password123"), "organizer"),
            ("pedromartinez", "pedro.martinez@example.com", "Pedro Martínez", hash_password("password123"),
             "participant"),
        ]

        user_ids = []
        for username, email, full_name, password_hash, role in users_data:
            cursor.callproc("CreateUser", (username, email, full_name, password_hash, role))
            for result in cursor.stored_results():
                user_id = result.fetchone()["user_id"]
                user_ids.append(user_id)
                print(f"✅ Usuario creado: {username} (ID: {user_id})")

        connection.commit()

        # ============== 2. EVENTOS ==============
        print("\n📅 Creando eventos...")

        # Eventos próximos
        upcoming_events = [
            (
                "Conferencia de Tecnología 2025",
                "La conferencia más grande de tecnología del año. Expertos internacionales compartirán las últimas tendencias en IA, Cloud Computing y Ciberseguridad.",
                datetime.now() + timedelta(days=30),
                "Centro de Convenciones Capital",
                500,
                user_ids[0]  # admin
            ),
            (
                "Workshop de Python Avanzado",
                "Taller práctico sobre técnicas avanzadas de Python: decoradores, generadores, context managers y más.",
                datetime.now() + timedelta(days=15),
                "Universidad Tecnológica - Sala 101",
                50,
                user_ids[2]  # mariagarcia
            ),
            (
                "Hackathon 2025",
                "48 horas de programación intensiva. Forma tu equipo y crea soluciones innovadoras para problemas reales.",
                datetime.now() + timedelta(days=45),
                "Tech Hub Innovation Center",
                100,
                user_ids[4]  # anasilva
            ),
            (
                "Meetup de Desarrollo Web",
                "Networking y charlas sobre las últimas tecnologías web: React, Vue, Next.js y más.",
                datetime.now() + timedelta(days=7),
                "Coworking Space Downtown",
                80,
                user_ids[2]  # mariagarcia
            ),
            (
                "Seminario de Machine Learning",
                "Introducción práctica a Machine Learning con Python. Incluye ejercicios con scikit-learn y TensorFlow.",
                datetime.now() + timedelta(days=20),
                "Centro de Capacitación TechEdu",
                60,
                user_ids[0]  # admin
            ),
        ]

        # Eventos pasados
        past_events = [
            (
                "Conferencia DevOps 2024",
                "Evento sobre mejores prácticas de DevOps, CI/CD y automatización.",
                datetime.now() - timedelta(days=30),
                "Hotel Convention Center",
                200,
                user_ids[4]  # anasilva
            ),
            (
                "Workshop de Docker y Kubernetes",
                "Taller práctico sobre contenedores y orquestación.",
                datetime.now() - timedelta(days=15),
                "Tech Academy",
                40,
                user_ids[2]  # mariagarcia
            ),
            (
                "Meetup de Desarrollo Móvil",
                "Charlas sobre Flutter, React Native y desarrollo móvil nativo.",
                datetime.now() - timedelta(days=7),
                "Startup Hub",
                70,
                user_ids[0]  # admin
            ),
        ]

        event_ids = []

        for title, description, date, location, max_participants, organizer_id in upcoming_events + past_events:
            cursor.callproc("CreateEvent", (title, description, date, location, max_participants, organizer_id))
            for result in cursor.stored_results():
                event_id = result.fetchone()["event_id"]
                event_ids.append(event_id)
                print(f"✅ Evento creado: {title} (ID: {event_id})")

        connection.commit()

        # ============== 3. ASISTENCIAS ==============
        print("\n🎫 Registrando asistencias...")

        # Usuarios asisten a eventos próximos
        attendances = [
            # Conferencia de Tecnología 2025
            (user_ids[1], event_ids[0]),  # juanperez
            (user_ids[2], event_ids[0]),  # mariagarcia
            (user_ids[3], event_ids[0]),  # carloslopez
            (user_ids[5], event_ids[0]),  # pedromartinez

            # Workshop de Python Avanzado
            (user_ids[1], event_ids[1]),  # juanperez
            (user_ids[3], event_ids[1]),  # carloslopez
            (user_ids[5], event_ids[1]),  # pedromartinez

            # Hackathon 2025
            (user_ids[1], event_ids[2]),  # juanperez
            (user_ids[3], event_ids[2]),  # carloslopez

            # Meetup de Desarrollo Web
            (user_ids[1], event_ids[3]),  # juanperez
            (user_ids[5], event_ids[3]),  # pedromartinez

            # Eventos pasados (marcados como attended)
            (user_ids[1], event_ids[5]),  # juanperez - DevOps
            (user_ids[3], event_ids[5]),  # carloslopez - DevOps
            (user_ids[5], event_ids[6]),  # pedromartinez - Docker
            (user_ids[1], event_ids[7]),  # juanperez - Móvil
        ]

        for user_id, event_id in attendances:
            cursor.callproc("RegisterAttendance", (user_id, event_id))
            print(f"✅ Asistencia registrada: Usuario {user_id} -> Evento {event_id}")

        connection.commit()

        # ============== 4. COMENTARIOS Y CALIFICACIONES ==============
        print("\n💬 Creando comentarios...")

        comments = [
            # Eventos pasados
            (user_ids[1], event_ids[5],
             "Excelente conferencia, aprendí muchísimo sobre DevOps y CI/CD. Los speakers fueron de primer nivel.", 5),
            (user_ids[3], event_ids[5], "Muy buen evento, aunque me hubiera gustado más tiempo para networking.", 4),
            (
            user_ids[5], event_ids[6], "El workshop fue muy práctico. Los ejercicios con Docker me ayudaron mucho.", 5),
            (user_ids[1], event_ids[7], "Interesante meetup, especialmente la charla sobre Flutter.", 4),

            # Eventos próximos (comentarios anticipados)
            (user_ids[1], event_ids[0], "¡No puedo esperar por esta conferencia! Ya tengo mi entrada.", 5),
            (user_ids[2], event_ids[0], "Los speakers confirmados se ven increíbles. Definitivamente asistiré.", 5),
            (user_ids[3], event_ids[1], "Espero que cubran async/await en profundidad.", 4),
        ]

        for user_id, event_id, content, rating in comments:
            cursor.callproc("CreateComment", (user_id, event_id, content, rating))
            print(f"✅ Comentario creado: Usuario {user_id} -> Evento {event_id}")

        connection.commit()

        # ============== 5. COMPARTICIONES DE EVENTOS ==============
        print("\n🔗 Registrando comparticiones...")

        shares = [
            (event_ids[0], "social_media", None),
            (event_ids[0], "email", "amigos@example.com"),
            (event_ids[1], "social_media", None),
            (event_ids[2], "social_media", None),
            (event_ids[2], "email", "equipo@example.com"),
            (event_ids[3], "social_media", None),
            (event_ids[4], "email", "colegas@example.com"),
        ]

        for event_id, share_type, recipient in shares:
            cursor.callproc("LogEventShare", (event_id, share_type, recipient))
            print(f"✅ Compartición registrada: Evento {event_id} -> {share_type}")

        connection.commit()

        # ============== 6. AUTENTICACIÓN SOCIAL ==============
        print("\n🔐 Creando registros de OAuth...")

        social_auths = [
            (user_ids[1], "google", "google_123456789"),
            (user_ids[3], "facebook", "facebook_987654321"),
        ]

        for user_id, provider, provider_id in social_auths:
            cursor.execute(
                "INSERT INTO social_auth (user_id, provider, provider_id) VALUES (%s, %s, %s)",
                (user_id, provider, provider_id)
            )
            print(f"✅ OAuth creado: Usuario {user_id} -> {provider}")

        connection.commit()

        print("\n✨ ¡Seed completado exitosamente!")
        print("\n📊 Resumen:")
        print(f"   - {len(users_data)} usuarios creados")
        print(f"   - {len(upcoming_events) + len(past_events)} eventos creados")
        print(f"   - {len(attendances)} asistencias registradas")
        print(f"   - {len(comments)} comentarios creados")
        print(f"   - {len(shares)} comparticiones registradas")
        print(f"   - {len(social_auths)} autenticaciones sociales")

        print("\n🔑 Credenciales de prueba:")
        print("   Admin:")
        print("     Usuario: admin")
        print("     Password: admin123")
        print("   Usuario regular:")
        print("     Usuario: juanperez")
        print("     Password: password123")

    except Error as e:
        print(f"❌ Error: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n✅ Conexión cerrada")


if __name__ == "__main__":
    seed_database()