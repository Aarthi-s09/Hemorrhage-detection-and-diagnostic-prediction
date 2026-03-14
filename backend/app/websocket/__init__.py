"""
WebSocket Connection Manager for Real-time Notifications
"""
from typing import Dict, List, Set
from fastapi import WebSocket
import json
from datetime import datetime


class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications
    """
    
    def __init__(self):
        # Map of user_id to list of active connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Set of all active websocket objects
        self.all_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.all_connections.add(websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to notification service",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up empty user entry
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        self.all_connections.discard(websocket)
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user's connections"""
        if user_id in self.active_connections:
            message["timestamp"] = datetime.utcnow().isoformat()
            disconnected = []
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, user_id)
    
    async def send_to_users(self, message: dict, user_ids: List[int]):
        """Send a message to multiple users"""
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users"""
        message["timestamp"] = datetime.utcnow().isoformat()
        disconnected = []
        
        for websocket in self.all_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up - find user_id for disconnected websockets
        for ws in disconnected:
            for user_id, connections in list(self.active_connections.items()):
                if ws in connections:
                    self.disconnect(ws, user_id)
                    break
    
    async def send_critical_alert(self, scan_id: str, patient_name: str, severity: float, doctor_ids: List[int]):
        """Send critical hemorrhage alert to doctors"""
        message = {
            "type": "critical_alert",
            "priority": "critical",
            "data": {
                "scan_id": scan_id,
                "patient_name": patient_name,
                "severity": severity,
                "message": f"⚠️ CRITICAL: Severe hemorrhage detected ({severity:.1f}% spread) - Immediate attention required"
            }
        }
        await self.send_to_users(message, doctor_ids)
    
    async def send_scan_complete(self, scan_id: str, has_hemorrhage: bool, user_id: int):
        """Notify user that scan analysis is complete"""
        message = {
            "type": "scan_complete",
            "priority": "medium" if not has_hemorrhage else "high",
            "data": {
                "scan_id": scan_id,
                "has_hemorrhage": has_hemorrhage,
                "message": f"Scan {scan_id} analysis complete. {'Hemorrhage detected.' if has_hemorrhage else 'No hemorrhage detected.'}"
            }
        }
        await self.send_personal_message(message, user_id)
    
    async def send_report_notification(self, report_id: str, doctor_id: int, is_critical: bool):
        """Notify doctor about new report"""
        message = {
            "type": "new_report",
            "priority": "critical" if is_critical else "medium",
            "data": {
                "report_id": report_id,
                "is_critical": is_critical,
                "message": f"New report {report_id} received. {'URGENT - Immediate review required!' if is_critical else 'Please review at your convenience.'}"
            }
        }
        await self.send_personal_message(message, doctor_id)
    
    def get_connected_users(self) -> List[int]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if a user has active connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Global connection manager instance
connection_manager = ConnectionManager()
