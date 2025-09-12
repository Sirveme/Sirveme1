from pydantic import BaseModel
from typing import List, Optional

class ClienteInfo(BaseModel):
    tipo_documento: Optional[str] = "DNI"
    numero_documento: Optional[str] = None
    nombre: Optional[str] = None
    direccion: Optional[str] = None

class ItemPedidoCreate(BaseModel):
    producto_id: int
    cantidad: int
    variante_id: Optional[int] = None
    # --- NUEVO: Lista de IDs de las opciones de modificador elegidas ---
    modificadores_seleccionados: List[int] = []
    nota_cocina: Optional[str] = None

class PedidoCreate(BaseModel):
    items: List[ItemPedidoCreate]
    cliente: ClienteInfo
    # --- AÑADIR ESTAS DOS LÍNEAS ---
    mesa_id: Optional[int] = None
    zona_id: Optional[int] = None
    # En el futuro, podríamos recibir aquí: mesa_id, notas, etc.

class PedidoConfirmadoResponse(BaseModel):
    id: int
    total: float
    estado: str
    mensaje: str

class RespuestaProcesoPedido(BaseModel):
    """
    Define la estructura de la respuesta que el backend enviará
    al frontend después de iniciar el proceso de pedido.
    """
    status: str  # Será 'enviado_a_cocina' o 'pago_requerido'
    mensaje: str
    
    # Campos opcionales que solo se enviarán cuando sea necesario
    pedido_id: Optional[int] = None
    cuenta_id: Optional[int] = None
    url_pago: Optional[str] = None # Para el futuro, con una pasarela real

class PedidoEstadoUpdate(BaseModel):
    """
    Esquema para recibir la actualización de estado de un pedido desde el KDS.
    """
    nuevo_estado: str # Recibimos el estado como string (ej: "LISTO_PARA_RECOGER")