# app/servicios/servicio_producto.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.db.modelos import modelos_core
from app.esquemas import esquemas_producto

def get_productos_por_negocio(db: Session, negocio_id: int) -> List[modelos_core.Producto]:
    """
    Obtiene todos los productos asociados a un negocio.
    """
    return db.query(modelos_core.Producto).filter(modelos_core.Producto.negocio_id == negocio_id).all()

def crear_producto(db: Session, producto: esquemas_producto.ProductoCreate, negocio_id: int) -> modelos_core.Producto:
    """
    Crea un nuevo producto y sus variantes (si las tiene) para un negocio.
    """
    # Extraemos las variantes del objeto Pydantic
    variantes_data = producto.variantes
    # Creamos una copia del diccionario del producto sin las variantes
    producto_data = producto.model_dump(exclude={'variantes'})

    db_producto = modelos_core.Producto(**producto_data, negocio_id=negocio_id)
    
    # Si se enviaron variantes, las creamos y las asociamos al producto
    if variantes_data:
        for variante_data in variantes_data:
            db_variante = modelos_core.VarianteProducto(**variante_data.model_dump())
            db_producto.variantes.append(db_variante)

    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

# --- Añadiremos más funciones (get_categorias, update, delete) aquí a medida que las necesitemos ---
def get_categorias_por_negocio(db: Session, negocio_id: int) -> List[modelos_core.Categoria]:
    """
    Obtiene todas las categorías asociadas a un negocio.
    """
    return db.query(modelos_core.Categoria).filter(modelos_core.Categoria.negocio_id == negocio_id).all()

def crear_categoria(db: Session, categoria: esquemas_producto.CategoriaCreate, negocio_id: int) -> modelos_core.Categoria:
    """
    Crea una nueva categoría para un negocio.
    """
    db_categoria = modelos_core.Categoria(**categoria.model_dump(), negocio_id=negocio_id)
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def get_producto_por_id(db: Session, *, producto_id: int, negocio_id: int) -> modelos_core.Producto:
    """
    Obtiene un producto específico por su ID, asegurándose de que pertenezca al negocio correcto.
    Carga eficientemente sus variantes.
    """
    return db.query(modelos_core.Producto).options(
        joinedload(modelos_core.Producto.variantes)
    ).filter(
        modelos_core.Producto.id == producto_id,
        modelos_core.Producto.negocio_id == negocio_id
    ).first()

def actualizar_producto(db: Session, db_producto: modelos_core.Producto, producto_in: esquemas_producto.ProductoUpdate):
    """
    Actualiza un producto y sincroniza sus variantes.
    """
    # Actualizar campos básicos
    for key, value in producto_in.model_dump(exclude_unset=True, exclude={'variantes'}).items():
        setattr(db_producto, key, value)

    # Manejar las variantes
    if producto_in.tiene_variantes:
        # Sincronizamos las variantes existentes en la BD con las enviadas en la petición
        variantes_existentes = db_producto.variantes
        variantes_actualizadas = producto_in.variantes

        # 1. Eliminar variantes que ya no están en la lista de actualización
        variantes_a_mantener_nombres = {v.nombre for v in variantes_actualizadas}
        for variante in list(variantes_existentes): # Hacemos una copia para evitar problemas de iteración
            if variante.nombre not in variantes_a_mantener_nombres:
                db.delete(variante)
                
        # 2. Actualizar o crear variantes
        for variante_data in variantes_actualizadas:
            # Buscamos la variante existente por nombre
            variante_existente = next((v for v in variantes_existentes if v.nombre == variante_data.nombre), None)

            if variante_existente:
                # Actualizamos si existe
                variante_existente.precio = variante_data.precio
                # Aquí podrías añadir el SKU si lo implementaste en el modelo
            else:
                # Creamos si no existe
                db_variante = modelos_core.VarianteProducto(**variante_data.model_dump())
                db_producto.variantes.append(db_variante)
    else:
        # Si tiene_variantes es False, eliminamos todas las variantes existentes
        db_producto.variantes = []
        
    db.commit()
    db.refresh(db_producto)
    return db_producto