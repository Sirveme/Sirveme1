# app/db/modelos/modelos_pedidos.py
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Enum as SQLAlchemyEnum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .modelos_financieros import Cuenta

from app.db.conexion import Base

# Tabla de asociación para Detalle <-> OpcionModificador
detalle_pedido_modificadores = Table('detalle_pedido_modificadores', Base.metadata,
    Column('detalle_pedido_id', Integer, ForeignKey('detalles_pedido.id'), primary_key=True),
    Column('opcion_modificador_id', Integer, ForeignKey('opciones_modificadores.id'), primary_key=True)
)

class EstadoPedido(enum.Enum):
    PENDIENTE_DE_PAGO = "PENDIENTE_DE_PAGO"
    PENDIENTE = "PENDIENTE"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO_PARA_RECOGER = "LISTO_PARA_RECOGER"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"

class Pedido(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey('negocios.id'), nullable=False)
    mesa_id = Column(Integer, ForeignKey('mesas.id'), nullable=True)
    mozo_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True) # Mozo es un Usuario
    cuenta_id = Column(Integer, ForeignKey('cuentas.id'), nullable=False) # Cada pedido PERTENECE a una cuenta
    alias_cliente = Column(String(100), nullable=True) # Para cobros en efectivo

    total_pedido = Column(Numeric(10, 2), nullable=False) # Total solo de este pedido
    estado = Column(SQLAlchemyEnum(EstadoPedido), nullable=False, default=EstadoPedido.PENDIENTE)
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    cuenta = relationship("Cuenta", back_populates="pedidos")
    detalles = relationship("DetallePedido", cascade="all, delete-orphan")

class DetallePedido(Base):
    __tablename__ = 'detalles_pedido'

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    variante_id = Column(Integer, ForeignKey('variantes_producto.id'), nullable=True)
    
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    nombre_producto = Column(String, nullable=False)
    nombre_variante = Column(String, nullable=True)
    nota_cocina = Column(String(255), nullable=True)
    
    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto")
    variante = relationship("VarianteProducto")
    modificadores_seleccionados = relationship("OpcionModificador", secondary=detalle_pedido_modificadores)