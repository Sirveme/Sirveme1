#BACKUP DEL 1 DE SETIEMBRE A LAS 20:25 😁
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal
import json
from collections import defaultdict

# Importaciones estandarizadas
from app.db.modelos import modelos_core
from app.db.modelos import modelos_pedidos
from app.db.modelos import modelos_financieros
from app.esquemas import esquemas_pedido
from app.core.websocket_manager import manager


async def crear_nuevo_pedido(
    db: Session, 
    negocio_id: int, 
    pedido_data: esquemas_pedido.PedidoCreate,
    estado_inicial: modelos_pedidos.EstadoPedido = modelos_pedidos.EstadoPedido.PENDIENTE
) -> modelos_pedidos.Pedido:
    
    # 1. Calcular el total del pedido y preparar los detalles
    total_pedido = Decimal('0.00')
    detalles_a_crear = []
    
    for item_in in pedido_data.items:
        # Hacemos un joinload para traer el centro de producción en la misma consulta
        producto = db.query(modelos_core.Producto).options(
            joinedload(modelos_core.Producto.centro_produccion)
        ).filter(modelos_core.Producto.id == item_in.producto_id).first()

        if not producto:
            raise ValueError(f"Producto con ID {item_in.producto_id} no encontrado.")

        precio_unitario = Decimal('0.00')
        nombre_variante = None

        if item_in.variante_id:
            variante = db.query(modelos_core.VarianteProducto).filter(
                modelos_core.VarianteProducto.id == item_in.variante_id,
                modelos_core.VarianteProducto.producto_id == producto.id
            ).first()
            if not variante:
                raise ValueError(f"Variante con ID {item_in.variante_id} no encontrada para el producto {producto.nombre}.")
            precio_unitario = variante.precio
            nombre_variante = variante.nombre
        else:
            if producto.tiene_variantes:
                raise ValueError(f"El producto '{producto.nombre}' requiere que se especifique una variante.")
            precio_unitario = producto.precio_base
        
        precio_modificadores = Decimal('0.00')
        modificadores_db = []
        if item_in.modificadores_seleccionados:
            opciones = db.query(modelos_core.OpcionModificador).filter(modelos_core.OpcionModificador.id.in_(item_in.modificadores_seleccionados)).all()
            for opcion in opciones:
                precio_modificadores += opcion.precio_extra
                modificadores_db.append(opcion)

        total_item = (precio_unitario + precio_modificadores) * item_in.cantidad
        total_pedido += total_item
        
        detalle_obj = modelos_pedidos.DetallePedido(
            producto_id=item_in.producto_id,
            variante_id=item_in.variante_id,
            cantidad=item_in.cantidad,
            precio_unitario=precio_unitario,
            nombre_producto=producto.nombre,
            nombre_variante=nombre_variante,
            nota_cocina=item_in.nota_cocina,
            modificadores_seleccionados=modificadores_db
        )
        detalle_obj.producto = producto # Asociamos el objeto producto completo para usarlo después
        detalles_a_crear.append(detalle_obj)

    if not detalles_a_crear:
        raise ValueError("El pedido no puede estar vacío.")

    # 2. Buscar una cuenta abierta para esa mesa o crear una nueva
    cuenta = db.query(modelos_financieros.Cuenta).filter(
        modelos_financieros.Cuenta.mesa_id == pedido_data.mesa_id,
        modelos_financieros.Cuenta.estado == modelos_financieros.EstadoCuenta.ABIERTA
    ).first()

    if not cuenta:
        cuenta = modelos_financieros.Cuenta(
            negocio_id=negocio_id,
            mesa_id=pedido_data.mesa_id,
            zona_id=pedido_data.zona_id,
            estado=modelos_financieros.EstadoCuenta.ABIERTA,
            total_calculado=Decimal('0.00')
        )
        db.add(cuenta)
    
    # 3. Actualizar el total de la cuenta (sumando el nuevo pedido)
    cuenta.total_calculado = (cuenta.total_calculado or Decimal('0.00')) + total_pedido
    db.flush() 
    
    # 4. Crear el PEDIDO y asociarlo a la cuenta
    nuevo_pedido = modelos_pedidos.Pedido(
        negocio_id=negocio_id,
        mesa_id=pedido_data.mesa_id,
        cuenta_id=cuenta.id,
        total_pedido=total_pedido,
        estado=estado_inicial,
        detalles=detalles_a_crear
    )

    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)
    db.refresh(cuenta)

    # 5. LÓGICA DE WEBSOCKETS (AGRUPADA POR CENTRO DE PRODUCCIÓN)
    comandos_por_centro = defaultdict(list)
    for detalle in nuevo_pedido.detalles:
        # Ya no necesitamos consultar la BD de nuevo, el objeto 'producto' está asociado
        if hasattr(detalle, 'producto') and detalle.producto and detalle.producto.centro_produccion_id:
            centro_id = str(detalle.producto.centro_produccion_id)
            comandos_por_centro[centro_id].append({
                "nombre": detalle.nombre_producto,
                "cantidad": detalle.cantidad,
                "nota": detalle.nota_cocina
            })

    # Enviar un mensaje WebSocket separado para cada centro de producción
    for centro_id, items in comandos_por_centro.items():
        mensaje_kds = {
            "mesa_id": nuevo_pedido.mesa_id,
            "pedido_id": nuevo_pedido.id,
            "items": items,
            "fecha_creacion": nuevo_pedido.fecha_creacion.isoformat()
        }
        await manager.broadcast(json.dumps(mensaje_kds), client_id=centro_id)

    return nuevo_pedido