from fastapi import APIRouter, HTTPException, Depends
import mysql.connector
from app.models.social_models import CommentCreate, CommentResponse, ShareEvent, ShareEventResponse, CommentUpdate
from app.database.connection import get_db

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