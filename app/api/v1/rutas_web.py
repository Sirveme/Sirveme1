# app/api/v1/rutas_web.py
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

# --- IMPORTACIONES ESTANDARIZADAS ---
from app.core.app_setup import templates
from app.db.conexion import SessionLocal
from app.api.v1.rutas_usuarios import get_current_user
from app.db.modelos import modelos_core, modelos_operativos
from app.api.v1.rutas_superadmin import get_super_usuario

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Sirve la página de login, pasando la configuración de la marca a la plantilla.
    """
    # El middleware ya ha hecho el trabajo. Solo leemos la configuración del 'state'.
    brand_config = request.state.brand_config
    
    # Renderizamos la plantilla, pasándole el objeto 'request' (requerido por Jinja2)
    # y nuestra configuración de marca.
    context = {
        "request": request,
        "brand_config": brand_config
    }
    return templates.TemplateResponse("login.html", context)

@router.get("/panel", response_class=HTMLResponse)
def get_panel_page(
    request: Request,
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    """
    Sirve la página principal del panel (Dashboard).
    """
    brand_config = request.state.brand_config
    
    # --- DATOS DE EJEMPLO AMPLIADOS ---
    dashboard_data = {
        "ventas_hoy": 2847.30,
        "comparacion_ayer": 12.5,
        "pedidos_activos": 18,
        "promedio_diario": 15,
        "alertas_stock": 5,
        "clientes_atendidos": 142
    }

    # --- NUEVOS DATOS PARA "ACTIVIDAD RECIENTE" ---
    actividad_reciente = [
        {"tipo": "venta", "descripcion": "Venta completada - Mesa 12", "monto": 85.50, "hace": "5 minutos"},
        {"tipo": "stock", "descripcion": "Stock bajo - Pollo a la brasa", "detalle": "Quedan 8 unidades", "hace": "15 minutos"},
        {"tipo": "gasto", "descripcion": "Registrado gasto - Compra de verduras", "monto": 120.00, "hace": "1 hora"}
    ]

    context = {
        "request": request,
        "current_user": current_user,
        "brand_config": brand_config,
        "dashboard_data": dashboard_data,
        "actividad_reciente": actividad_reciente # <-- NUEVO DATO
    }
    return templates.TemplateResponse("panel/dashboard.html", context)


@router.get("/panel/kds/{centro_id}", response_class=HTMLResponse)
def get_kds_page(
    request: Request,
    centro_id: int,
    db: Session = Depends(get_db),
    current_user: modelos_core.Usuario = Depends(get_current_user) # Usamos la referencia completa
):
    """
    Sirve la página del Monitor de Cocina/Barra (KDS).
    """
    # 1. Buscar el centro de producción en la base de datos
    centro_produccion = db.query(modelos_operativos.CentroProduccion).filter(
        modelos_operativos.CentroProduccion.id == centro_id,
        modelos_operativos.CentroProduccion.negocio_id == current_user.negocio_id
    ).first()

    if not centro_produccion:
        raise HTTPException(status_code=404, detail="Centro de producción no encontrado o no pertenece a este negocio.")

    # 2. Obtener el local del usuario para mostrarlo
    local_usuario = None
    if current_user.local_asignado_id:
        # --- CONSULTA CORREGIDA Y SINTÁCTICAMENTE CORRECTA ---
        local_usuario = db.query(modelos_core.Local).filter(modelos_core.Local.id == current_user.local_asignado_id).first()
    
    if not local_usuario:
        # Si el usuario no tiene un local asignado (o no se encontró), no puede ver el KDS
        raise HTTPException(status_code=403, detail="El usuario no tiene un local asignado para ver este KDS.")

    brand_config = request.state.brand_config
    context = {
        "request": request,
        "current_user": current_user,
        "brand_config": brand_config,
        "centro_produccion": centro_produccion,
        "local_usuario": local_usuario
    }
    return templates.TemplateResponse("panel/kds.html", context)


@router.get("/panel/superadmin/negocios", response_class=HTMLResponse)
def get_gestion_negocios_page(
    request: Request,
    current_user: modelos_core.Usuario = Depends(get_super_usuario) # Protegido
):
    """
    Sirve la página de gestión de negocios para el Super-Admin.
    """
    brand_config = request.state.brand_config
    context = {
        "request": request,
        "current_user": current_user,
        "brand_config": brand_config
    }
    return templates.TemplateResponse("superadmin/gestion_negocios.html", context)


@router.get("/panel/configuracion", response_class=HTMLResponse)
def get_configuracion_page(
    request: Request,
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    """
    Sirve la página de configuración del negocio para el rol 'Dueño'.
    """
    if current_user.rol.nombre != 'Dueño':
        return RedirectResponse(url="/panel", status_code=status.HTTP_303_SEE_OTHER)

    brand_config = request.state.brand_config
    context = {
        "request": request,
        "current_user": current_user,
        "brand_config": brand_config
    }
    return templates.TemplateResponse("panel/configuracion.html", context)


@router.get("/panel/personal", response_class=HTMLResponse)
def get_personal_page(
    request: Request,
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    """
    Sirve la página de gestión de personal.
    (En el futuro, protegeremos esta ruta por permiso, no por rol).
    """
    if current_user.rol.nombre not in ['Dueño', 'SuperUsuario']:
        # Redirigir a una página de "acceso denegado" o al dashboard
        return RedirectResponse(url="/panel", status_code=status.HTTP_303_SEE_OTHER)

    brand_config = request.state.brand_config
    context = {
        "request": request,
        "current_user": current_user,
        "brand_config": brand_config
    }
    return templates.TemplateResponse("panel/personal.html", context)