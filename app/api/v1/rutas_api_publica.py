from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from typing import List
from urllib.parse import unquote

# Importaciones estandarizadas y centralizadas
from app.core.app_setup import templates
from app.db.conexion import SessionLocal
from app.db.modelos import modelos_core, modelos_pedidos
from app.esquemas import esquemas_carta, esquemas_pedido
from app.servicios import servicio_llm, servicio_pedido

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === RUTA PARA MOSTRAR LA CARTA (GET) ===


# === RUTA PARA PROCESAR VOZ/TEXTO (POST) ===
@router.post("/carta/{slug_negocio}/parse-orden-voz")
def parse_orden_voz(
    slug_negocio: str,
    orden: esquemas_carta.OrdenVozRequest,
    db: Session = Depends(get_db)
):
    nombre_decodificado = unquote(slug_negocio)
    negocio = db.query(modelos_core.Negocio).filter(modelos_core.Negocio.nombre_comercial == nombre_decodificado).first()
    if not negocio:
        raise HTTPException(status_code=404, detail=f"No se encontró el negocio '{nombre_decodificado}'")

    print(f"\n--- INICIO DIAGNÓSTICO parse-orden-voz ---") # <-- LOG 1: Inicio
    print(f"Texto recibido del cliente: '{orden.texto_orden}'")
    
    productos_db = db.query(modelos_core.Producto).options(
        # ... (joinedloads sin cambios)
    ).filter(modelos_core.Producto.negocio_id == negocio.id, modelos_core.Producto.activo == True).all()

    print(f"Productos encontrados en BD para este negocio: {[p.nombre for p in productos_db]}") # <-- LOG 2: Productos de la BD

    if not productos_db:
        return {"intent": "UNKNOWN", "entities": []}

    menu_simple_para_llm = [
        {"id": p.id, "nombre": p.nombre, "alias": p.alias} for p in productos_db
    ]
    
    print(f"Menú simple enviado al LLM: {menu_simple_para_llm}") # <-- LOG 3: Menú para el LLM

    resultado_llm = servicio_llm.procesar_orden_con_llm(menu_simple_para_llm, orden.texto_orden)
    
    print(f"Respuesta recibida del LLM: {resultado_llm}") # <-- LOG 4: Respuesta del LLM
    print(f"--- FIN DIAGNÓSTICO ---\n")

    if resultado_llm.get("entities"):
        for entity in resultado_llm["entities"]:
            producto_completo_encontrado = next((p for p in productos_db if p.id == entity.get("product_id")), None)
            if producto_completo_encontrado:
                entity["full_product_data"] = esquemas_carta.ItemFormulario.model_validate(producto_completo_encontrado).model_dump()

    return resultado_llm

# === RUTA PARA CONFIRMAR PEDIDO (POST) ===
@router.post("/carta/{slug_negocio}/{zona_id}/{mesa_id}/iniciar-proceso-pedido", response_model=esquemas_pedido.RespuestaProcesoPedido)
async def iniciar_proceso_pedido(
    slug_negocio: str,
    zona_id: int,
    mesa_id: int,
    pedido_in: esquemas_pedido.PedidoCreate,
    db: Session = Depends(get_db)
):
    nombre_decodificado = unquote(slug_negocio)
    negocio = db.query(modelos_core.Negocio).filter(modelos_core.Negocio.nombre_comercial == nombre_decodificado).first()
    if not negocio:
        raise HTTPException(status_code=404, detail=f"No se encontró el negocio '{nombre_decodificado}'")
    
    pedido_in.zona_id = zona_id
    pedido_in.mesa_id = mesa_id
    
    if negocio.modo_cobro == 'POSTPAGO':
        try:
            # === CAMBIO 2: Usar 'await' para llamar a la función asíncrona ===
            nuevo_pedido = await servicio_pedido.crear_nuevo_pedido(db=db, negocio_id=negocio.id, pedido_data=pedido_in)
            return esquemas_pedido.RespuestaProcesoPedido(
                status="enviado_a_cocina",
                mensaje=f"¡Pedido #{nuevo_pedido.id} confirmado! Ya estamos preparando tu orden.",
                pedido_id=nuevo_pedido.id,
                cuenta_id=nuevo_pedido.cuenta_id
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    elif negocio.modo_cobro == 'PREPAGO':
        try:
            pedido_pendiente = await servicio_pedido.crear_nuevo_pedido(db=db, negocio_id=negocio.id, pedido_data=pedido_in, estado_inicial=modelos_pedidos.EstadoPedido.PENDIENTE_DE_PAGO)
            url_pago_simulada = f"/pagar/{pedido_pendiente.cuenta_id}"
            return esquemas_pedido.RespuestaProcesoPedido(
                status="pago_requerido",
                mensaje="Tu pedido está listo. Por favor, realiza el pago para enviarlo a cocina.",
                cuenta_id=pedido_pendiente.cuenta_id,
                url_pago=url_pago_simulada
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    else:
        raise HTTPException(status_code=500, detail="Modo de cobro no configurado correctamente para este negocio.")