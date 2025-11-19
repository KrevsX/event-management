from fastapi import APIRouter, HTTPException, Depends
from app.services.oauth_service import OAuthService
from app.database.connection import get_db
import mysql.connector
from app.models.user_models import UserRole

router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.post("/google")
async def oauth_google(access_token: str, role: UserRole = UserRole.PARTICIPANT,
                       db: mysql.connector.MySQLConnection = Depends(get_db)):
    try:
        # Obtener información del usuario de Google
        user_info = await OAuthService.get_google_user_info(access_token)

        # Buscar o crear usuario
        user_id = OAuthService.find_or_create_user_from_oauth(
            provider="google",
            provider_id=user_info["sub"],
            email=user_info["email"],
            name=user_info["name"],
            role=role.value,
            db=db
        )

        return {
            "message": "Google OAuth successful",
            "user_id": user_id,
            "email": user_info["email"],
            "name": user_info["name"],
            "role": role.value
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/facebook")
async def oauth_facebook(access_token: str, role: UserRole = UserRole.PARTICIPANT,
                         db: mysql.connector.MySQLConnection = Depends(get_db)):
    try:
        # Obtener información del usuario de Facebook
        user_info = await OAuthService.get_facebook_user_info(access_token)

        # Buscar o crear usuario
        user_id = OAuthService.find_or_create_user_from_oauth(
            provider="facebook",
            provider_id=user_info["id"],
            email=user_info.get("email", f"{user_info['id']}@facebook.com"),
            name=user_info["name"],
            role=role.value,
            db=db
        )

        return {
            "message": "Facebook OAuth successful",
            "user_id": user_id,
            "email": user_info.get("email"),
            "name": user_info["name"],
            "role": role.value
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))