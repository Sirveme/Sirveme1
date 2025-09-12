from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Numeric, UniqueConstraint, NUMERIC
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.conexion import Base

# Importaciones de nuestros otros módulos de modelos
from .modelos_operativos import CentroProduccion
from .modelos_configuracion import MetodoPagoLocal

# --- TABLAS DE ASOCIACIÓN ---
rol_permisos = Table('rol_permisos', Base.metadata,
    Column('rol_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permiso_id', Integer, ForeignKey('permisos.id'), primary_key=True)
)

producto_grupo_modificador_tabla = Table('producto_grupo_modificador', Base.metadata,
    Column('producto_id', Integer, ForeignKey('productos.id'), primary_key=True),
    Column('grupo_modificador_id', Integer, ForeignKey('grupos_modificadores.id'), primary_key=True)
)

# --- NUEVA TABLA: Catálogo de Productos por Local ---
producto_locales_tabla = Table('producto_locales', Base.metadata,
    Column('producto_id', Integer, ForeignKey('productos.id'), primary_key=True),
    Column('local_id', Integer, ForeignKey('locales.id'), primary_key=True),
    Column('disponible', Boolean, default=True, nullable=False),
    Column('precio_local', Numeric(10, 2), nullable=True) # Para sobreescribir el precio base
)


# --- CLASES DE MODELOS ---

class Permiso(Base):
    __tablename__ = "permisos"
    # ... (sin cambios)
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(100), unique=True, index=True, nullable=False)
    descripcion = Column(String(255))
    roles = relationship("Rol", secondary=rol_permisos, back_populates="permisos")

class Rol(Base):
    __tablename__ = "roles"
    # ... (sin cambios)
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    descripcion = Column(String(255))
    usuarios = relationship("Usuario", back_populates="rol")
    permisos = relationship("Permiso", secondary=rol_permisos, back_populates="roles")

class Negocio(Base):
    __tablename__ = "negocios"
    id = Column(Integer, primary_key=True, index=True)
    ruc = Column(String(11), unique=True, index=True, nullable=False)
    razon_social = Column(String(255), nullable=False)
    nombre_comercial = Column(String(255))
    marca_origen = Column(String(50), nullable=False)
    activo = Column(Boolean, default=True)
    modo_cobro = Column(String(20), nullable=False, server_default='POSTPAGO')
    
    # --- NUEVOS CAMPOS DE CONFIGURACIÓN ---
    tema_id = Column(Integer, ForeignKey("temas.id"), nullable=True)
    logo_url = Column(String(255), nullable=True)
    
     # --- RELACIONES ---
    tema = relationship("Tema", back_populates="negocios")
    locales = relationship("Local", back_populates="negocio", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="negocio")

class Local(Base):
    __tablename__ = "locales"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255))
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    
    # --- NUEVO CAMPO DE CONTACTO ---
    telefono_contacto = Column(String(20), nullable=True)

    # --- NUEVAS RELACIONES ---
    negocio = relationship("Negocio", back_populates="locales")
    zonas = relationship("Zona", back_populates="local", cascade="all, delete-orphan")
    metodos_pago = relationship("MetodoPagoLocal", back_populates="local", cascade="all, delete-orphan")
    productos_disponibles = relationship("Producto", secondary=producto_locales_tabla, back_populates="locales_disponibles")

class Zona(Base):
    __tablename__ = "zonas"
    # ... (sin cambios)
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    local_id = Column(Integer, ForeignKey("locales.id"), nullable=False)
    local = relationship("Local", back_populates="zonas")
    mesas = relationship("Mesa", back_populates="zona", cascade="all, delete-orphan")

class Mesa(Base):
    __tablename__ = "mesas"
    # ... (sin cambios)
    id = Column(Integer, primary_key=True, index=True)
    nombre_o_numero = Column(String(50), nullable=False)
    capacidad = Column(Integer, default=0)
    zona_id = Column(Integer, ForeignKey("zonas.id"), nullable=False)
    zona = relationship("Zona", back_populates="mesas")
    
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    tipo_documento = Column(String(10), nullable=False, index=True)
    numero_documento = Column(String(20), nullable=False, index=True)
    nombre_completo = Column(String(255), nullable=False)
    foto_url = Column(String(255), nullable=True)
    sueldo_base = Column(Numeric(10, 2), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    telefono = Column(String(20), unique=True, index=True, nullable=False)
    password_hashed = Column(String(255), nullable=False)
    reset_password_token = Column(String(10), nullable=True)
    reset_password_token_expires = Column(DateTime(timezone=True), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    negocio_id = Column(Integer, ForeignKey("negocios.id"))
    
    # --- NUEVA ASIGNACIÓN DE LOCAL ---
    local_asignado_id = Column(Integer, ForeignKey("locales.id"), nullable=True)

    rol = relationship("Rol", back_populates="usuarios")
    negocio = relationship("Negocio", back_populates="usuarios")

class Categoria(Base):
    __tablename__ = "categorias"
    # ... (sin cambios)
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    negocio = relationship("Negocio")
    productos = relationship("Producto", back_populates="categoria")

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    alias = Column(String(255), nullable=True)
    tipo_producto = Column(String(20), default="PLATO", nullable=False) # 'PLATO' o 'BEBIDA'
    descripcion = Column(String(500))
    precio_base = Column(Numeric(10, 2), nullable=False)
    tiene_variantes = Column(Boolean, default=False, nullable=False)
    sku = Column(String(50), unique=True, nullable=True, index=True)
    activo = Column(Boolean, default=True)
    imagen_url = Column(String(255))
    
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    centro_produccion_id = Column(Integer, ForeignKey("centros_produccion.id"), nullable=True)
    
     # --- RELACIÓN CORREGIDA Y DEFINITIVA ---
    # Le decimos: "Yo soy 'centro_produccion', y la propiedad en la clase 'CentroProduccion' que me corresponde es 'productos'".
    centro_produccion = relationship("CentroProduccion", back_populates="productos")

    categoria = relationship("Categoria", back_populates="productos")
    negocio = relationship("Negocio")
    variantes = relationship("VarianteProducto", back_populates="producto", cascade="all, delete-orphan")
    grupos_modificadores = relationship("GrupoModificador", secondary="producto_grupo_modificador", back_populates="productos")
    
    # --- NUEVA RELACIÓN ---
    locales_disponibles = relationship("Local", secondary=producto_locales_tabla, back_populates="productos_disponibles")
    
class VarianteProducto(Base):
    __tablename__ = "variantes_producto"
    # ... (sin cambios)
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    sku = Column(String(50), unique=True, nullable=True, index=True)
    stock = Column(Integer)
    producto = relationship("Producto", back_populates="variantes")
    __table_args__ = (UniqueConstraint('producto_id', 'nombre', name='_producto_variante_uc'),)

class GrupoModificador(Base):
    __tablename__ = "grupos_modificadores"
    # ... (sin cambios)
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    seleccion_minima = Column(Integer, nullable=False, default=1)
    seleccion_maxima = Column(Integer, nullable=False, default=1)
    opciones = relationship("OpcionModificador", back_populates="grupo", cascade="all, delete-orphan")
    productos = relationship("Producto", secondary="producto_grupo_modificador", back_populates="grupos_modificadores")
    
class OpcionModificador(Base):
    __tablename__ = "opciones_modificadores"
    # ... (sin cambios)
    id = Column(Integer, primary_key=True, index=True)
    grupo_id = Column(Integer, ForeignKey("grupos_modificadores.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    precio_extra = Column(Numeric(10, 2), default=0.00)
    grupo = relationship("GrupoModificador", back_populates="opciones")


class Proveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True, index=True)
    negocio_id = Column(Integer, ForeignKey("negocios.id"), nullable=False)
    ruc = Column(String(11), nullable=False)
    razon_social = Column(String(255), nullable=False)
    nombre_contacto = Column(String(255), nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)