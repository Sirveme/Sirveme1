from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.conexion import Base

class TipoFeedback(enum.Enum):
    QUEJA = "QUEJA"
    SUGERENCIA = "SUGERENCIA"
    FELICITACION = "FELICITACION"

class FeedbackCliente(Base):
    __tablename__ = 'feedback_cliente'
    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey('negocios.id'), nullable=False)
    mesa_id = Column(Integer, ForeignKey('mesas.id'), nullable=True)
    
    tipo = Column(SQLAlchemyEnum(TipoFeedback), nullable=False)
    mensaje = Column(Text, nullable=False)
    contacto_cliente = Column(String(255), nullable=True) # Opcional, si el cliente deja email/teléfono
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())