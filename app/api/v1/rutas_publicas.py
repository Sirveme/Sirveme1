# Endpoints para la carta virtual y vistas de cliente
# app/api/v1/rutas_publicas.py
from fastapi import APIRouter, Request, Depends, HTTPException, Body
from pydantic import BaseModel

from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from app.core.app_setup import templates
from app.db.conexion import SessionLocal
from app.db.modelos import modelos_core
from app.db.modelos import modelos_configuracion, modelos_operativos

from app.esquemas import esquemas_configuracion

from typing import List, Optional
from urllib.parse import unquote

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/carta/{slug_negocio}/{zona_id}/{mesa_id}", response_class=HTMLResponse)
def get_carta_virtual(
    request: Request,
    slug_negocio: str,
    zona_id: int,
    mesa_id: int,
    db: Session = Depends(get_db)
):
    nombre_decodificado = unquote(slug_negocio)
    negocio = db.query(modelos_core.Negocio).filter(modelos_core.Negocio.nombre_comercial == nombre_decodificado).first()
    if not negocio:
        raise HTTPException(status_code=404, detail=f"No se encontró el negocio '{nombre_decodificado}'.")
    
    mesa = db.query(modelos_core.Mesa).filter(modelos_core.Mesa.id == mesa_id).first()
    zona = db.query(modelos_core.Zona).filter(modelos_core.Zona.id == zona_id).first()
    if not mesa or not zona:
         raise HTTPException(status_code=404, detail="La mesa o zona especificadas no existen.")
        
    categorias = db.query(modelos_core.Categoria).options(
        joinedload(modelos_core.Categoria.productos).joinedload(modelos_core.Producto.variantes)
    ).filter(modelos_core.Categoria.negocio_id == negocio.id).all()

    brand_config = request.state.brand_config
    
    context = {
        "request": request,
        "negocio": negocio,
        "categorias": categorias,
        "brand_config": brand_config,
        "mesa_id": mesa_id,
        "zona_id": zona_id
    }
    return templates.TemplateResponse("public/carta_virtual.html", context)


# === AÑADE ESTA NUEVA RUTA ===
@router.get("/temas", response_model=List[esquemas_configuracion.Tema])
def get_lista_temas(db: Session = Depends(get_db)):
    """
    Devuelve la lista de todos los temas disponibles en el sistema.
    Es una ruta pública para que cualquiera pueda ver los temas.
    """
    temas = db.query(modelos_configuracion.Tema).all()
    return temas


# === RUTA PARA LA PÁGINA HOME ===
@router.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request):
    """
    Sirve la nueva página de inicio (landing page).
    """
    brand_config = request.state.brand_config
    context = {"request": request, "brand_config": brand_config}
    return templates.TemplateResponse("public/home.html", context)

