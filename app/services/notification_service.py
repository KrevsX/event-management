"""
Servicio de gestión de notificaciones con estado de lectura
Sin modificar la base de datos - usa almacenamiento en memoria
"""
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional
from pydantic import BaseModel


class NotificationReadStatus:
    """
    Almacena en memoria qué notificaciones han sido leídas por cada usuario
    Key: user_id -> Set de notification_ids leídos
    """
    _read_notifications: Dict[int, Set[str]] = {}

    @classmethod
    def mark_as_read(cls, user_id: int, notification_id: str) -> bool:
        """Marca una notificación como leída"""
        if user_id not in cls._read_notifications:
            cls._read_notifications[user_id] = set()

        cls._read_notifications[user_id].add(notification_id)
        return True

    @classmethod
    def mark_multiple_as_read(cls, user_id: int, notification_ids: List[str]) -> int:
        """Marca múltiples notificaciones como leídas"""
        if user_id not in cls._read_notifications:
            cls._read_notifications[user_id] = set()

        cls._read_notifications[user_id].update(notification_ids)
        return len(notification_ids)

    @classmethod
    def is_read(cls, user_id: int, notification_id: str) -> bool:
        """Verifica si una notificación ha sido leída"""
        return notification_id in cls._read_notifications.get(user_id, set())

    @classmethod
    def get_read_notifications(cls, user_id: int) -> Set[str]:
        """Obtiene todas las notificaciones leídas de un usuario"""
        return cls._read_notifications.get(user_id, set())

    @classmethod
    def get_unread_count(cls, user_id: int, all_notification_ids: List[str]) -> int:
        """Cuenta cuántas notificaciones no leídas tiene un usuario"""
        read_ids = cls._read_notifications.get(user_id, set())
        return len([nid for nid in all_notification_ids if nid not in read_ids])

    @classmethod
    def clear_user_notifications(cls, user_id: int) -> bool:
        """Limpia todas las notificaciones leídas de un usuario"""
        if user_id in cls._read_notifications:
            del cls._read_notifications[user_id]
            return True
        return False

    @classmethod
    def mark_all_as_read(cls, user_id: int, notification_ids: List[str]) -> int:
        """Marca todas las notificaciones como leídas"""
        return cls.mark_multiple_as_read(user_id, notification_ids)


class NotificationService:
    """Servicio para generar y gestionar notificaciones"""

    @staticmethod
    def generate_notification_id(user_id: int, event_id: int, notification_type: str) -> str:
        """
        Genera un ID único para la notificación
        Formato: {user_id}_{event_id}_{type}_{date}
        """
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{user_id}_{event_id}_{notification_type}_{date_str}"

    @staticmethod
    def create_notification_dict(
            user_id: int,
            event_id: int,
            event_title: str,
            event_date: datetime,
            event_location: str,
            notification_type: str,
            message: str,
            days_until_event: Optional[int] = None,
            changes: Optional[List[str]] = None
    ) -> dict:
        """Crea un diccionario de notificación con estado de lectura"""

        notification_id = NotificationService.generate_notification_id(
            user_id, event_id, notification_type
        )

        # Verificar si está leída
        is_read = NotificationReadStatus.is_read(user_id, notification_id)

        notification = {
            "notification_id": notification_id,
            "event_id": event_id,
            "event_title": event_title,
            "event_date": event_date,
            "event_location": event_location,
            "notification_type": notification_type,
            "message": message,
            "days_until_event": days_until_event,
            "open": 0 if is_read else 1,  # 0 = leída, 1 = no leída
            "created_at": datetime.now()
        }

        if changes:
            notification["changes"] = changes

        return notification

    @staticmethod
    def get_reminder_notifications(cursor, user_id: int) -> List[dict]:
        """Obtiene notificaciones de recordatorio para un usuario"""
        cursor.execute("""
            SELECT e.*, ea.registered_at
            FROM event_attendance ea
            JOIN events e ON ea.event_id = e.id
            WHERE ea.user_id = %s AND e.is_active = TRUE AND e.date >= NOW()
            ORDER BY e.date ASC
        """, (user_id,))

        user_events = cursor.fetchall()
        notifications = []

        for event in user_events:
            event_date = event['date']
            now = datetime.now()

            time_until_event = event_date - now
            days_until = time_until_event.days
            hours_until = time_until_event.total_seconds() / 3600

            # Notificación de recordatorio (24 horas antes)
            if 0 <= hours_until <= 24:
                notification = NotificationService.create_notification_dict(
                    user_id=user_id,
                    event_id=event['id'],
                    event_title=event['title'],
                    event_date=event['date'],
                    event_location=event['location'],
                    notification_type="reminder",
                    message=f"¡Recordatorio! El evento '{event['title']}' es mañana a las {event['date'].strftime('%H:%M')} en {event['location']}",
                    days_until_event=0 if hours_until < 24 else 1
                )
                notifications.append(notification)

            # Información general del evento próximo
            elif days_until > 0:
                notification = NotificationService.create_notification_dict(
                    user_id=user_id,
                    event_id=event['id'],
                    event_title=event['title'],
                    event_date=event['date'],
                    event_location=event['location'],
                    notification_type="upcoming",
                    message=f"Tienes confirmada tu asistencia al evento '{event['title']}' el {event['date'].strftime('%d/%m/%Y')}",
                    days_until_event=days_until
                )
                notifications.append(notification)

        return notifications


# Modelos Pydantic para las requests
class MarkAsReadRequest(BaseModel):
    notification_id: str


class MarkMultipleAsReadRequest(BaseModel):
    notification_ids: List[str]


class NotificationStatsResponse(BaseModel):
    user_id: int
    total_notifications: int
    unread_count: int
    read_count: int