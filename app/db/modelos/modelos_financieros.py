import enum
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.conexion import Base

class EstadoCuenta(enum.Enum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA" # Pendiente de pago
    PAGADA = "PAGADA"
    CANCELADA = "CANCELADA"

class MedioDePago(enum.Enum):
    TARJETA_CREDITO = "TARJETA_CREDITO"
    TARJETA_DEBITO = "TARJETA_DEBITO"
    YAPE = "YAPE"
    PLIN = "PLIN"
    EFECTIVO = "EFECTIVO"
    OTRO = "OTRO"

class EstadoTransaccion(enum.Enum):
    EXITOSA = "EXITOSA"
    FALLIDA = "FALLIDA"
    PENDIENTE = "PENDIENTE"

class Cuenta(Base):
    __tablename__ = 'cuentas'
    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey('negocios.id'), nullable=False)
    mesa_id = Column(Integer, ForeignKey('mesas.id'), nullable=True) # Una cuenta puede estar asociada a una mesa
    zona_id = Column(Integer, ForeignKey('zonas.id'), nullable=True)
    usuario_cliente_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True) # O a un cliente registrado

    estado = Column(SQLAlchemyEnum(EstadoCuenta), nullable=False, default=EstadoCuenta.ABIERTA)
    total_calculado = Column(Numeric(10, 2), nullable=False, default=0.00)
    propina = Column(Numeric(10, 2), nullable=True, default=0.00)
    
    fecha_apertura = Column(DateTime(timezone=True), server_default=func.now())
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    zona = relationship("Zona")
    pedidos = relationship("Pedido", back_populates="cuenta")
    transacciones = relationship("Transaccion", back_populates="cuenta")
    mesa = relationship("Mesa")

class Transaccion(Base):
    __tablename__ = 'transacciones'
    id = Column(Integer, primary_key=True, index=True)
    cuenta_id = Column(Integer, ForeignKey('cuentas.id'), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    medio_de_pago = Column(SQLAlchemyEnum(MedioDePago), nullable=False)
    estado = Column(SQLAlchemyEnum(EstadoTransaccion), nullable=False, default=EstadoTransaccion.PENDIENTE)
    
    # Para guardar el ID de operación de la pasarela de pago (Izipay, etc.)
    referencia_externa = Column(String(255), nullable=True)
    fecha_transaccion = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    cuenta = relationship("Cuenta", back_populates="transacciones")