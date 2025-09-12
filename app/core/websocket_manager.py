from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Diccionario para guardar conexiones por centro de producción (Cocina, Barra, etc.)
        # Formato: {"cocina": [ws1, ws2], "barra": [ws3]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        print(f"WS Conexión activa: {client_id}. Total: {len(self.active_connections[client_id])}")

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections and websocket in self.active_connections[client_id]:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_text(message)

manager = ConnectionManager()