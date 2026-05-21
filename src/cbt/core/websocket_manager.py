from typing import Dict, List
from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        # Maps examination_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, examination_id: str):
        await websocket.accept()
        if examination_id not in self.active_connections:
            self.active_connections[examination_id] = []
        self.active_connections[examination_id].append(websocket)

    def disconnect(self, websocket: WebSocket, examination_id: str):
        if examination_id in self.active_connections:
            if websocket in self.active_connections[examination_id]:
                self.active_connections[examination_id].remove(websocket)
            if not self.active_connections[examination_id]:
                del self.active_connections[examination_id]

    async def broadcast_to_examination(self, examination_id: str, message: dict):
        if examination_id in self.active_connections:
            for connection in list(self.active_connections[examination_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection, examination_id)

manager = ConnectionManager()
