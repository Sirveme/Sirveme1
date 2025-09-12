from pydantic import BaseModel
from typing import Optional, List
from . import esquemas_core # Importamos para usar los esquemas

class Tema(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    url_vista_previa_dark: Optional[str] = None
    url_vista_previa_light: Optional[str] = None
    class Config: from_attributes = True

class MetodoPago(BaseModel):
    id: int
    nombre_metodo: str
    datos_adicionales: Optional[dict] = None
    class Config: from_attributes = True

class LocalConMetodos(esquemas_core.Local): # Heredamos de esquemas_core.Local
    metodos_pago: List[MetodoPago] = []
    class Config: from_attributes = True