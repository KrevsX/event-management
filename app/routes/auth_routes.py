from fastapi import APIRouter, HTTPException, Depends
import mysql.connector
from app.models.user_models import UserCreate, UserLogin, UserResponse, SocialAuth, UserUpdate
from app.utils.security import hash_password, verify_password
from app.database.connection import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    try:
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                       (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")

        # Crear usuario - convertir role a string si es Enum
        hashed_password = hash_password(user.password)
        role_str = user.role.value if hasattr(user.role, 'value') else user.role

        cursor.callproc("CreateUser", (
            user.username,
            user.email,
            user.full_name,
            hashed_password,
            role_str
        ))

        # Obtener el user_id del resultado del stored procedure
        user_id = None
        for result in cursor.stored_results():
            user_result = result.fetchone()
            user_id = user_result["user_id"] if user_result else None

        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")

        db.commit()

        # Obtener usuario creado
        cursor.callproc("GetUserById", (user_id,))
        user_data = None
        for result in cursor.stored_results():
            user_data = result.fetchone()

        if not user_data:
            raise HTTPException(status_code=500, detail="Failed to retrieve created user")

        cursor.close()
        return UserResponse(**user_data)

    except mysql.connector.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        if cursor:
            cursor.close()


@router.post("/login")
async def login_user(login_data: UserLogin, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("GetUserByUsername", (login_data.username,))
    for result in cursor.stored_results():
        user_data = result.fetchone()

    if not user_data or not verify_password(login_data.password, user_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    cursor.close()
    return {"message": "Login successful", "user_id": user_data["id"]}


@router.get("/users", response_model=list)
async def get_all_users(db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    try:
        cursor.callproc("GetAllUsers")
        users = []
        for result in cursor.stored_results():
            users = result.fetchall()

        cursor.close()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("GetUserById", (user_id,))
    for result in cursor.stored_results():
        user_data = result.fetchone()

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.close()
    return UserResponse(**user_data)


@router.put("/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    try:
        # Hash password si se proporciona
        password_hash = None
        if user_update.password:
            password_hash = hash_password(user_update.password)

        # Convertir role a string si existe
        role_str = None
        if user_update.role:
            role_str = user_update.role.value if hasattr(user_update.role, 'value') else user_update.role

        cursor.callproc("UpdateUser", (
            user_id,
            user_update.username,
            user_update.email,
            user_update.full_name,
            password_hash,
            role_str
        ))

        db.commit()
        cursor.close()
        return {"message": "User updated successfully"}
    except mysql.connector.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("DeleteUser", (user_id,))
    db.commit()
    cursor.close()
    return {"message": "User deleted successfully"}


@router.post("/social-auth")
async def social_auth(social_data: SocialAuth, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    # Verificar si ya existe autenticación social
    cursor.execute("SELECT user_id FROM social_auth WHERE provider = %s AND provider_id = %s",
                   (social_data.provider, social_data.provider_id))
    existing_auth = cursor.fetchone()

    if existing_auth:
        user_id = existing_auth["user_id"]
    else:
        # Crear nuevo usuario o vincular con existente
        cursor.execute("SELECT id FROM users WHERE email = %s", (social_data.email,))
        existing_user = cursor.fetchone()

        if existing_user:
            user_id = existing_user["id"]
        else:
            # Crear nuevo usuario con rol
            username = social_data.email.split('@')[0]
            # Verificar si el username ya existe
            base_username = username
            counter = 1
            while True:
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if not cursor.fetchone():
                    break
                username = f"{base_username}{counter}"
                counter += 1

            cursor.callproc("CreateUser", (
                username, social_data.email, social_data.full_name, "oauth_password", social_data.role.value))
            for result in cursor.stored_results():
                user_id = result.fetchone()["user_id"]

        # Vincular autenticación social
        cursor.execute("INSERT INTO social_auth (user_id, provider, provider_id) VALUES (%s, %s, %s)",
                       (user_id, social_data.provider, social_data.provider_id))

    db.commit()
    cursor.close()
    return {"message": "Social authentication successful", "user_id": user_id}