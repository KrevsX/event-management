import httpx
from fastapi import HTTPException
from app.database.connection import get_db
import mysql.connector
from config import settings


class OAuthService:
    @staticmethod
    async def get_google_user_info(access_token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Google access token")
            return response.json()

    @staticmethod
    async def get_facebook_user_info(access_token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/me?fields=id,name,email&access_token={access_token}"
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Facebook access token")
            return response.json()

    @staticmethod
    def find_or_create_user_from_oauth(provider: str, provider_id: str, email: str, name: str, role: str, db):
        cursor = db.cursor(dictionary=True)

        try:
            # Buscar si ya existe autenticación social
            cursor.execute(
                "SELECT user_id FROM social_auth WHERE provider = %s AND provider_id = %s",
                (provider, provider_id)
            )
            existing_auth = cursor.fetchone()

            if existing_auth:
                user_id = existing_auth["user_id"]
            else:
                # Buscar usuario por email
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    user_id = existing_user["id"]
                else:
                    # Crear nuevo usuario
                    username = email.split('@')[0]
                    # Asegurar que el username sea único
                    base_username = username
                    counter = 1
                    while True:
                        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                        if not cursor.fetchone():
                            break
                        username = f"{base_username}{counter}"
                        counter += 1

                    cursor.execute(
                        "INSERT INTO users (username, email, full_name, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
                        (username, email, name, "oauth_password", role)
                    )
                    user_id = cursor.lastrowid

                # Crear registro de autenticación social
                cursor.execute(
                    "INSERT INTO social_auth (user_id, provider, provider_id) VALUES (%s, %s, %s)",
                    (user_id, provider, provider_id)
                )

            db.commit()
            return user_id

        except mysql.connector.Error as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            cursor.close()