from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db.conexion import Base

class MetodoPagoLocal(Base):
    __tablename__ = 'metodos_pago_local'
    id = Column(Integer, primary_key=True, index=True)
    local_id = Column(Integer, ForeignKey('locales.id'), nullable=False)
    nombre_metodo = Column(String(50), nullable=False) # Ej: "YAPE", "VISA", "EFECTIVO"
    
    # Campo flexible para guardar datos como el número de Yape, QR, etc.
    datos_adicionales = Column(JSON, nullable=True)

    local = relationship("Local", back_populates="metodos_pago")


class Tema(Base):
    __tablename__ = 'temas'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255))
    es_premium = Column(Boolean, default=False, nullable=False)
    url_vista_previa_dark = Column(String(255), nullable=True)
    url_vista_previa_light = Column(String(255), nullable=True)

    variables_css = relationship("VariableCssTema", back_populates="tema", cascade="all, delete-orphan")
    negocios = relationship("Negocio", back_populates="tema")

class VariableCssTema(Base):
    __tablename__ = 'variables_css_tema'
    id = Column(Integer, primary_key=True, index=True)
    tema_id = Column(Integer, ForeignKey('temas.id'), nullable=False)
    nombre_variable = Column(String(50), nullable=False) # ej: "--primary-color"
    valor_dark = Column(String(50), nullable=False)      # ej: "#00f7ff"
    valor_light = Column(String(50), nullable=False)     # ej: "#00aacc"

    tema = relationship("Tema", back_populates="variables_css")