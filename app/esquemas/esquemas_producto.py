# app/esquemas/esquemas_producto.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from decimal import Decimal

# --- Categoria Schemas ---
class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Producto Schemas ---
class VarianteProductoBase(BaseModel):
    nombre: str
    precio: Decimal
    sku: Optional[str] = None

class VarianteProductoCreate(VarianteProductoBase):
    pass

class ProductoBase(BaseModel):
    nombre: str
    tipo_producto: str = "preparado" # Añadido con valor por defecto
    descripcion: Optional[str] = None
    # precio_base es opcional, solo se usa si no hay variantes
    precio_base: Optional[Decimal] = 0.00 
    activo: bool = True
    categoria_id: int
    tiene_variantes: bool = False
    sku: Optional[str] = None

class ProductoCreate(ProductoBase):
    tipo_producto: str
    # Al crear, podemos recibir una lista opcional de variantes
    variantes: Optional[List[VarianteProductoCreate]] = []

class ProductoUpdate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int
    # Podríamos añadir aquí la categoría completa si quisiéramos
    categoria: Categoria
    model_config = ConfigDict(from_attributes=True)