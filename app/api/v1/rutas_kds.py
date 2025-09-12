from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.websocket_manager import manager

router = APIRouter()

# La ruta usa el ID del centro de producción (ej: 1 para Cocina, 2 para Barra)
@router.websocket("/ws/kds/{center_id}")
async def websocket_endpoint(websocket: WebSocket, center_id: str):
    await manager.connect(websocket, center_id)
    try:
        # Mantener la conexión abierta para recibir pings (aunque este KDS solo emite)
        while True:
            data = await websocket.receive_text()
            # Opcional: si el KDS envía un mensaje de "Comanda Lista", lo procesaríamos aquí
    except WebSocketDisconnect:
        manager.disconnect(websocket, center_id)
        print(f"Cliente {center_id} desconectado.")