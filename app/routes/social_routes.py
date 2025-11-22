from fastapi import APIRouter, HTTPException, Depends
import mysql.connector
from app.models.social_models import CommentCreate, CommentResponse, ShareEvent, ShareEventResponse, CommentUpdate
from app.database.connection import get_db
from datetime import datetime

# Importar el nuevo servicio de notificaciones
from app.services.notification_service import (
    NotificationService,
    NotificationReadStatus,
    MarkAsReadRequest,
    MarkMultipleAsReadRequest,
    NotificationStatsResponse
)

router = APIRouter(prefix="/social", tags=["Social Interaction"])

# ============== COMMENTS CRUD ==============

@router.post("/comments", response_model=CommentResponse)
async def create_comment(comment: CommentCreate, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    try:
        cursor.callproc("CreateComment", (
            comment.user_id, comment.event_id, comment.content, comment.rating
        ))

        for result in cursor.stored_results():
            comment_id = result.fetchone()["comment_id"]

        db.commit()

        # Obtener comentario creado
        cursor.execute("""
            SELECT c.*, u.username, u.full_name 
            FROM comments c 
            JOIN users u ON c.user_id = u.id 
            WHERE c.id = %s
        """, (comment_id,))
        comment_data = cursor.fetchone()

        cursor.close()
        return CommentResponse(**comment_data)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/comments/{comment_id}", response_model=CommentResponse)
async def get_comment(comment_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("GetCommentById", (comment_id,))
    for result in cursor.stored_results():
        comment_data = result.fetchone()

    if not comment_data:
        raise HTTPException(status_code=404, detail="Comment not found")

    cursor.close()
    return CommentResponse(**comment_data)


@router.get("/events/{event_id}/comments")
async def get_event_comments(event_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("GetEventComments", (event_id,))
    comments = []
    for result in cursor.stored_results():
        comments = result.fetchall()

    cursor.close()
    return {"comments": comments}


@router.get("/users/{user_id}/comments")
async def get_user_comments(user_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("GetCommentsByUser", (user_id,))
    comments = []
    for result in cursor.stored_results():
        comments = result.fetchall()

    cursor.close()
    return {"comments": comments}


@router.put("/comments/{comment_id}")
async def update_comment(comment_id: int, comment_update: CommentUpdate,
                         db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    try:
        cursor.callproc("UpdateComment", (
            comment_id,
            comment_update.content,
            comment_update.rating
        ))

        db.commit()
        cursor.close()
        return {"message": "Comment updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("DeleteComment", (comment_id,))
    db.commit()
    cursor.close()
    return {"message": "Comment deleted successfully"}


# ============== EVENT SHARES CRUD ==============

@router.post("/share", response_model=ShareEventResponse)
async def share_event(share_data: ShareEvent, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    try:
        cursor.callproc("LogEventShare", (
            share_data.event_id, share_data.share_type, share_data.recipient
        ))

        # IMPORTANTE: Obtener el lastrowid ANTES del commit
        share_id = cursor.lastrowid

        db.commit()

        # Si no obtuvimos ID, intentar obtenerlo de otra forma
        if not share_id or share_id == 0:
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            share_id = result['id'] if result else None

        if not share_id:
            raise HTTPException(status_code=500, detail="Failed to create share")

        # Obtener el share creado
        cursor.callproc("GetEventShareById", (share_id,))
        share_data_result = None
        for result in cursor.stored_results():
            share_data_result = result.fetchone()

        if not share_data_result:
            raise HTTPException(status_code=500, detail="Failed to retrieve created share")

        cursor.close()
        return ShareEventResponse(**share_data_result)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/shares/{share_id}", response_model=ShareEventResponse)
async def get_event_share(share_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("GetEventShareById", (share_id,))
    for result in cursor.stored_results():
        share_data = result.fetchone()

    if not share_data:
        raise HTTPException(status_code=404, detail="Share not found")

    cursor.close()
    return ShareEventResponse(**share_data)


@router.get("/events/{event_id}/shares")
async def get_event_shares(event_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("GetEventShares", (event_id,))
    shares = []
    for result in cursor.stored_results():
        shares = result.fetchall()

    cursor.close()
    return {"shares": shares}


@router.get("/shares")
async def get_all_shares(db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("GetAllEventShares")
    shares = []
    for result in cursor.stored_results():
        shares = result.fetchall()

    cursor.close()
    return {"shares": shares}


@router.delete("/shares/{share_id}")
async def delete_event_share(share_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.callproc("DeleteEventShare", (share_id,))
    db.commit()
    cursor.close()
    return {"message": "Share deleted successfully"}


@router.get("/notifications/user/{user_id}")
async def get_user_notifications(user_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """
    Obtiene notificaciones para un usuario con estado de lectura (open)
    - open=1: No leída
    - open=0: Leída
    """
    cursor = db.cursor(dictionary=True)

    try:
        # Obtener notificaciones usando el servicio
        notifications = NotificationService.get_reminder_notifications(cursor, user_id)

        # Contar no leídas
        unread_count = sum(1 for n in notifications if n['open'] == 1)

        cursor.close()
        return {
            "user_id": user_id,
            "total_notifications": len(notifications),
            "unread_count": unread_count,
            "read_count": len(notifications) - unread_count,
            "notifications": notifications
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/notifications/mark-as-read")
async def mark_notification_as_read(request: MarkAsReadRequest):
    """
    Marca una notificación como leída (open=0)
    Body: {"notification_id": "2_1_reminder_20251122"}
    """
    try:
        # Extraer user_id del notification_id
        parts = request.notification_id.split('_')
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid notification_id format")

        user_id = int(parts[0])

        # Marcar como leída
        success = NotificationReadStatus.mark_as_read(user_id, request.notification_id)

        if success:
            return {
                "message": "Notification marked as read",
                "notification_id": request.notification_id,
                "open": 0
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to mark notification as read")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/notifications/mark-multiple-as-read")
async def mark_multiple_notifications_as_read(request: MarkMultipleAsReadRequest):
    """
    Marca múltiples notificaciones como leídas
    Body: {"notification_ids": ["2_1_reminder_20251122", "2_3_upcoming_20251122"]}
    """
    try:
        if not request.notification_ids:
            raise HTTPException(status_code=400, detail="notification_ids cannot be empty")

        # Extraer user_id del primer notification_id
        parts = request.notification_ids[0].split('_')
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid notification_id format")

        user_id = int(parts[0])

        # Marcar todas como leídas
        count = NotificationReadStatus.mark_multiple_as_read(user_id, request.notification_ids)

        return {
            "message": f"{count} notifications marked as read",
            "notification_ids": request.notification_ids,
            "count": count
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/notifications/mark-all-as-read/{user_id}")
async def mark_all_notifications_as_read(user_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """
    Marca TODAS las notificaciones de un usuario como leídas
    """
    cursor = db.cursor(dictionary=True)

    try:
        # Obtener todas las notificaciones actuales
        notifications = NotificationService.get_reminder_notifications(cursor, user_id)

        # Extraer todos los IDs
        notification_ids = [n['notification_id'] for n in notifications]

        if not notification_ids:
            return {
                "message": "No notifications to mark as read",
                "user_id": user_id,
                "count": 0
            }

        # Marcar todas como leídas
        count = NotificationReadStatus.mark_all_as_read(user_id, notification_ids)

        cursor.close()
        return {
            "message": f"All {count} notifications marked as read",
            "user_id": user_id,
            "count": count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/notifications/stats/{user_id}", response_model=NotificationStatsResponse)
async def get_notification_stats(user_id: int, db: mysql.connector.MySQLConnection = Depends(get_db)):
    """
    Obtiene estadísticas de notificaciones de un usuario
    """
    cursor = db.cursor(dictionary=True)

    try:
        # Obtener notificaciones
        notifications = NotificationService.get_reminder_notifications(cursor, user_id)

        # Calcular estadísticas
        total = len(notifications)
        unread = sum(1 for n in notifications if n['open'] == 1)
        read = total - unread

        cursor.close()
        return NotificationStatsResponse(
            user_id=user_id,
            total_notifications=total,
            unread_count=unread,
            read_count=read
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/notifications/clear/{user_id}")
async def clear_user_read_notifications(user_id: int):
    """
    Limpia el historial de notificaciones leídas de un usuario
    Útil para resetear el estado
    """
    try:
        success = NotificationReadStatus.clear_user_notifications(user_id)

        if success:
            return {
                "message": "User notification history cleared",
                "user_id": user_id
            }
        else:
            return {
                "message": "No notification history to clear",
                "user_id": user_id
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/notifications/reminders")
async def get_event_reminders(db: mysql.connector.MySQLConnection = Depends(get_db)):
    """
    Obtiene todos los eventos que requieren recordatorio (próximas 24 horas)
    Útil para sistema de notificaciones automático
    """
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT e.*, u.username, u.email, u.full_name, ea.user_id
            FROM events e
            JOIN event_attendance ea ON e.id = ea.event_id
            JOIN users u ON ea.user_id = u.id
            WHERE e.is_active = TRUE 
            AND e.date BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 24 HOUR)
            ORDER BY e.date ASC
        """)

        reminders = cursor.fetchall()

        # Agrupar por evento
        events_with_attendees = {}
        for reminder in reminders:
            event_id = reminder['id']
            if event_id not in events_with_attendees:
                events_with_attendees[event_id] = {
                    "event_id": event_id,
                    "event_title": reminder['title'],
                    "event_date": reminder['date'],
                    "event_location": reminder['location'],
                    "attendees": []
                }

            events_with_attendees[event_id]["attendees"].append({
                "user_id": reminder['user_id'],
                "username": reminder['username'],
                "email": reminder['email'],
                "full_name": reminder['full_name']
            })

        cursor.close()
        return {
            "total_events": len(events_with_attendees),
            "events_needing_reminders": list(events_with_attendees.values())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")