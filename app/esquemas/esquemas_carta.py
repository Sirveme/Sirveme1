from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from decimal import Decimal

# --- Schemas para la Interacción de Voz y Carta ---

class VarianteInfo(BaseModel):
    id: int
    nombre: str
    precio: float
    model_config = ConfigDict(from_attributes=True)

class ModificadorInfo(BaseModel):
    id: int
    nombre: str
    precio_extra: float
    model_config = ConfigDict(from_attributes=True)

class GrupoModificadorInfo(BaseModel):
    id: int
    nombre: str
    seleccion_minima: int
    seleccion_maxima: int
    opciones: List[ModificadorInfo]
    model_config = ConfigDict(from_attributes=True)

# Este es el objeto que el frontend usará para construir una fila del formulario
class ItemFormulario(BaseModel):
    id: int
    nombre: str
    alias: Optional[str] = None
    precio_base: Optional[float] = None
    cantidad: int = 1
    
    # --- LA CORRECCIÓN CLAVE ---
    # Usamos un alias para que Pydantic sepa que 'variantes' en el modelo de BD
    # debe mapearse a 'variantes_disponibles' en este esquema.
    variantes_disponibles: List[VarianteInfo] = Field(alias='variantes', default=[])
    modificadores_disponibles: List[GrupoModificadorInfo] = Field(alias='grupos_modificadores', default=[])
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# La respuesta principal ahora es una lista de estos items de formulario
class RespuestaVozFormulario(BaseModel):
    items_formulario: List[ItemFormulario]

# Lo que el frontend envía al backend
class OrdenVozRequest(BaseModel):
    texto_orden: str

# Un item claro y sin ambigüedades, listo para el carrito
class ProductoEncontrado(BaseModel):
    nombre_producto: str
    nombre_variante: Optional[str] = None
    cantidad: int
    precio: float

# Una opción cuando el backend necesita que el usuario elija
class OpcionAclaracion(BaseModel):
    texto_display: str
    nombre_producto_base: str
    nombre_variante: str
    precio: float

# La respuesta completa que el backend envía al frontend
class RespuestaVoz(BaseModel):
    status: str  # 'success', 'requires_clarification', o 'not_found'
    items: List[ProductoEncontrado] = []
    mensaje_aclaracion: Optional[str] = None
    opciones_aclaracion: Optional[List[OpcionAclaracion]] = []