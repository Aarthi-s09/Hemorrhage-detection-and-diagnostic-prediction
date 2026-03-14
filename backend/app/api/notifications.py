"""
Notification API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationListResponse, NotificationMarkRead
from app.services.notification_service import NotificationService
from app.services.auth_service import AuthService
from app.utils.security import get_current_active_user
from app.websocket import connection_manager


router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user notifications"""
    notifications = NotificationService.get_user_notifications(
        db, current_user.id, unread_only=unread_only, limit=limit
    )
    unread_count = NotificationService.get_unread_count(db, current_user.id)
    
    return NotificationListResponse(
        notifications=notifications,
        total=len(notifications),
        unread_count=unread_count
    )


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get count of unread notifications"""
    count = NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.get("/critical", response_model=list[NotificationResponse])
async def get_critical_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get unread critical notifications"""
    notifications = NotificationService.get_critical_notifications(db, current_user.id)
    return notifications


@router.post("/mark-read")
async def mark_notifications_read(
    data: NotificationMarkRead,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark specific notifications as read"""
    updated = NotificationService.mark_as_read(db, data.notification_ids, current_user.id)
    return {"updated": updated}


@router.post("/mark-all-read")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all notifications as read"""
    updated = NotificationService.mark_all_as_read(db, current_user.id)
    return {"updated": updated}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a notification"""
    deleted = NotificationService.delete_notification(db, notification_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return {"deleted": True}


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time notifications"""
    # Validate token and get user
    payload = AuthService.decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user = AuthService.get_user_by_id(db, payload.sub)
    if not user or not user.is_active:
        await websocket.close(code=4001, reason="User not found or inactive")
        return
    
    # Connect
    await connection_manager.connect(websocket, user.id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user.id)
