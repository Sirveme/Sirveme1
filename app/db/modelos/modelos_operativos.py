from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.conexion import Base

class CentroProduccion(Base):
    __tablename__ = 'centros_produccion'
    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey('negocios.id'), nullable=False)
    nombre = Column(String(100), nullable=False)

    negocio = relationship("Negocio")
    
    # DEFINICIÓN EXPLÍCITA DE LA RELACIÓN
    # Le decimos: "Yo soy 'productos', y la propiedad en la clase 'Producto' que me corresponde es 'centro_produccion'".
    productos = relationship("Producto", back_populates="centro_produccion")