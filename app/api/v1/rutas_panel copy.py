from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import json

# Importaciones estandarizadas
from app.db.conexion import SessionLocal
from app.db.modelos import modelos_core, modelos_pedidos, modelos_operativos, modelos_financieros, modelos_configuracion
from app.esquemas import esquemas_core, esquemas_configuracion
from app.api.v1.rutas_usuarios import get_current_user, Usuario
from app.core.websocket_manager import manager

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PedidoEstadoUpdate(BaseModel):
    nuevo_estado: modelos_pedidos.EstadoPedido

@router.post("/panel/pedidos/{pedido_id}/actualizar-estado", status_code=200)
def actualizar_estado_pedido(
    pedido_id: int,
    estado_update: PedidoEstadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    pedido = db.query(modelos_pedidos.Pedido).filter(
        modelos_pedidos.Pedido.id == pedido_id,
        modelos_pedidos.Pedido.negocio_id == current_user.negocio_id
    ).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    
    pedido.estado = estado_update.nuevo_estado
    db.commit()
    db.refresh(pedido)
    return {"mensaje": "Estado del pedido actualizado con éxito.", "nuevo_estado": pedido.estado}

@router.post("/panel/pedidos/{pedido_id}/marcar-pagado", status_code=200)
async def marcar_pedido_como_pagado(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    pedido = db.query(modelos_pedidos.Pedido).options(
        joinedload(modelos_pedidos.Pedido.detalles).joinedload(modelos_pedidos.DetallePedido.producto)
    ).filter(
        modelos_pedidos.Pedido.id == pedido_id,
        modelos_pedidos.Pedido.negocio_id == current_user.negocio_id
    ).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    if pedido.estado != modelos_pedidos.EstadoPedido.PENDIENTE_DE_PAGO:
        raise HTTPException(status_code=400, detail="El pedido no está pendiente de pago.")
    
    pedido.estado = modelos_pedidos.EstadoPedido.PENDIENTE
    db.commit()
    db.refresh(pedido)

    comandos_por_centro = defaultdict(list)
    for detalle in pedido.detalles:
        if detalle.producto and detalle.producto.centro_produccion_id:
            centro_id = str(detalle.producto.centro_produccion_id)
            comandos_por_centro[centro_id].append({
                "nombre": detalle.nombre_producto, "cantidad": detalle.cantidad, "nota": detalle.nota_cocina
            })

    for centro_id, items in comandos_por_centro.items():
        mensaje_kds = {
            "mesa_id": pedido.mesa_id, "pedido_id": pedido.id,
            "total_pedido": float(pedido.total_pedido), "items": items,
            "fecha_creacion": pedido.fecha_creacion.isoformat()
        }
        await manager.broadcast(json.dumps(mensaje_kds), client_id=centro_id)
        
    return {"mensaje": f"Pedido #{pedido.id} marcado como pagado y enviado a producción."}


# --- ENDPOINTS PARA EL KDS INTELIGENTE (RECONSTRUIDOS) ---

def agrupar_pedidos_para_kds(pedidos: List[modelos_pedidos.Pedido], centro_id: int):
    resultado = defaultdict(lambda: {"mesa_id": 0, "fecha_creacion": None, "total_pedido": 0.0, "estado": "", "items": [], "total_cobrar": 0.0}) # <-- AÑADIR total_cobrar
    for pedido in pedidos:
        items_del_centro = []
        
        # Para Caja, mostramos todos los items del pedido pendiente de pago
        if pedido.estado == modelos_pedidos.EstadoPedido.PENDIENTE_DE_PAGO:
            items_del_centro = [{"nombre": det.nombre_producto, "cantidad": det.cantidad, "nota": det.nota_cocina} for det in pedido.detalles]
        else: # Para Cocina/Barra, solo los items que les corresponden
            for det in pedido.detalles:
                if det.producto and det.producto.centro_produccion_id == centro_id:
                    items_del_centro.append({"nombre": det.nombre_producto, "cantidad": det.cantidad, "nota": det.nota_cocina})
        
        if items_del_centro:
            info = resultado[pedido.id]
            info["mesa_id"] = pedido.mesa_id
            info["fecha_creacion"] = pedido.fecha_creacion.isoformat()
            info["total_pedido"] = float(pedido.total_pedido)
            info["estado"] = pedido.estado.value
            info["items"] = items_del_centro
            if pedido.estado == modelos_pedidos.EstadoPedido.PENDIENTE_DE_PAGO:
                info["total_cobrar"] = float(pedido.total_pedido) # <-- AÑADIR
            
    return [{"pedido_id": pid, **data} for pid, data in resultado.items()]

@router.get("/panel/kds/{centro_id}/pedidos-pendientes")
def get_pedidos_pendientes_kds(
    centro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    centro = db.query(modelos_operativos.CentroProduccion).get(centro_id)
    if not centro:
        raise HTTPException(status_code=404, detail="Centro de producción no encontrado.")

    estados_a_buscar = []
    if centro.nombre == 'Caja':
        estados_a_buscar.append(modelos_pedidos.EstadoPedido.PENDIENTE_DE_PAGO)
    else:
        estados_a_buscar.extend([modelos_pedidos.EstadoPedido.PENDIENTE, modelos_pedidos.EstadoPedido.EN_PREPARACION])

    pedidos_activos = db.query(modelos_pedidos.Pedido).options(
        joinedload(modelos_pedidos.Pedido.detalles).joinedload(modelos_pedidos.DetallePedido.producto)
    ).filter(
        modelos_pedidos.Pedido.negocio_id == current_user.negocio_id,
        modelos_pedidos.Pedido.estado.in_(estados_a_buscar)
    ).order_by(modelos_pedidos.Pedido.fecha_creacion.asc()).all()
    
    return agrupar_pedidos_para_kds(pedidos_activos, centro_id)

@router.get("/panel/kds/{centro_id}/pedidos-completados")
def get_pedidos_completados_kds(
    centro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    hoy = datetime.now(timezone.utc).date()
    pedidos_completados = db.query(modelos_pedidos.Pedido).options(
        joinedload(modelos_pedidos.Pedido.detalles).joinedload(modelos_pedidos.DetallePedido.producto)
    ).filter(
        modelos_pedidos.Pedido.negocio_id == current_user.negocio_id,
        modelos_pedidos.Pedido.estado == modelos_pedidos.EstadoPedido.LISTO_PARA_RECOGER,
        func.date(modelos_pedidos.Pedido.fecha_creacion) >= hoy
    ).order_by(modelos_pedidos.Pedido.fecha_creacion.desc()).all()
    
    return agrupar_pedidos_para_kds(pedidos_completados, centro_id)

@router.get("/panel/negocio/pedidos-en-espera")
def get_pedidos_mayor_espera(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Devuelve una lista de los 5 pedidos pendientes más antiguos.
    """
    from datetime import datetime, timezone, timedelta
    
    umbral_tiempo = datetime.now(timezone.utc) - timedelta(minutes=10)

    # --- CONSULTA CORREGIDA Y DEFINITIVA ---
    pedidos_demorados = db.query(modelos_pedidos.Pedido).options(
        # La ruta correcta: Carga la 'cuenta', y DENTRO de ella, carga la 'mesa', y DENTRO de ella, la 'zona'.
        joinedload(modelos_pedidos.Pedido.cuenta)
            .joinedload(modelos_financieros.Cuenta.mesa)
            .joinedload(modelos_core.Mesa.zona),
        joinedload(modelos_pedidos.Pedido.detalles)
    ).filter(
        modelos_pedidos.Pedido.negocio_id == current_user.negocio_id,
        modelos_pedidos.Pedido.estado.in_([
            modelos_pedidos.EstadoPedido.PENDIENTE,
            modelos_pedidos.EstadoPedido.EN_PREPARACION
        ]),
        modelos_pedidos.Pedido.fecha_creacion < umbral_tiempo
    ).order_by(modelos_pedidos.Pedido.fecha_creacion.asc()).limit(5).all()

    resultado = []
    ahora = datetime.now(timezone.utc)
    for pedido in pedidos_demorados:
        if not pedido.cuenta or not pedido.cuenta.mesa:
            continue # Omitir pedidos que no estén asociados a una mesa

        fecha_creacion_utc = pedido.fecha_creacion.replace(tzinfo=timezone.utc)
        tiempo_espera = ahora - fecha_creacion_utc
        minutos_espera = int(tiempo_espera.total_seconds() / 60)
        
        item_ejemplo = pedido.detalles[0].nombre_producto if pedido.detalles else "N/A"

        resultado.append({
            "mesa_nombre": pedido.cuenta.mesa.nombre_o_numero,
            "zona_nombre": pedido.cuenta.mesa.zona.nombre,
            "minutos_espera": minutos_espera,
            "item_ejemplo": item_ejemplo
        })
        
    return resultado

# --- ENDPOINTS DE CONFIGURACIÓN DEL NEGOCIO ---
@router.get("/panel/configuracion-negocio", response_model=esquemas_core.Negocio)
def get_configuracion_negocio(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    negocio = db.query(modelos_core.Negocio).options(
        joinedload(modelos_core.Negocio.locales)
    ).filter(modelos_core.Negocio.id == current_user.negocio_id).first()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado.")
    return negocio

@router.put("/panel/configuracion-negocio", response_model=esquemas_core.Negocio)
def update_configuracion_negocio(
    config_in: esquemas_core.NegocioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre != 'Dueño':
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar la configuración.")
    negocio = db.query(modelos_core.Negocio).filter(modelos_core.Negocio.id == current_user.negocio_id).first()
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado.")
    
    negocio.nombre_comercial = config_in.nombre_comercial
    negocio.modo_cobro = config_in.modo_cobro
    negocio.tema_id = config_in.tema_id
    negocio.logo_url = config_in.logo_url
    db.commit()
    db.refresh(negocio)
    return negocio

# --- ENDPOINTS PARA GESTIÓN DE LOCALES ---
@router.get("/panel/locales", response_model=List[esquemas_configuracion.LocalConMetodos])
def get_locales_del_negocio(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    locales = db.query(modelos_core.Local).options(
        joinedload(modelos_core.Local.metodos_pago)
    ).filter(modelos_core.Local.negocio_id == current_user.negocio_id).all()
    return locales

@router.put("/panel/locales/{local_id}", response_model=esquemas_configuracion.LocalConMetodos)
def update_local(
    local_id: int,
    local_in: esquemas_core.LocalUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre != 'Dueño':
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar locales.")
        
    local = db.query(modelos_core.Local).filter(
        modelos_core.Local.id == local_id,
        modelos_core.Local.negocio_id == current_user.negocio_id
    ).first()
    if not local:
        raise HTTPException(status_code=404, detail="Local no encontrado.")
        
    local.nombre = local_in.nombre
    local.direccion = local_in.direccion
    local.telefono_contacto = local_in.telefono_contacto
    db.commit()
    db.refresh(local)
    return local

# --- ENDPOINT PARA GESTIÓN DE MÉTODOS DE PAGO ---
@router.post("/panel/locales/{local_id}/metodos-pago", response_model=esquemas_configuracion.MetodoPago)
def add_metodo_pago_a_local(
    local_id: int,
    metodo_in: esquemas_core.MetodoPagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol.nombre != 'Dueño':
        raise HTTPException(status_code=403, detail="No tienes permiso para añadir métodos de pago.")
        
    local = db.query(modelos_core.Local).filter(
        modelos_core.Local.id == local_id,
        modelos_core.Local.negocio_id == current_user.negocio_id
    ).first()
    if not local:
        raise HTTPException(status_code=404, detail="Local no encontrado.")

    nuevo_metodo = modelos_configuracion.MetodoPagoLocal(
        local_id=local.id,
        nombre_metodo=metodo_in.nombre_metodo,
        datos_adicionales=metodo_in.datos_adicionales
    )
    db.add(nuevo_metodo)
    db.commit()
    db.refresh(nuevo_metodo)
    return nuevo_metodo