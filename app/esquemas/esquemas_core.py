from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List

# --- ESQUEMAS PARA RESPUESTAS (LEER DATOS DE LA BD) ---

class Permiso(BaseModel):
    id: int
    codigo: str
    descripcion: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class Rol(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    permisos: List[Permiso] = []
    model_config = ConfigDict(from_attributes=True)

class Usuario(BaseModel):
    id: int
    tipo_documento: str
    numero_documento: str
    nombre_completo: str
    telefono: str
    email: Optional[EmailStr] = None
    activo: bool
    rol_id: int
    negocio_id: Optional[int] = None
    local_asignado_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
    sueldo_base: Optional[float] = None
    
class Local(BaseModel):
    id: int
    nombre: str
    direccion: Optional[str] = None
    telefono_contacto: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class Negocio(BaseModel):
    id: int
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    activo: bool
    modo_cobro: str
    tema_id: Optional[int] = None
    logo_url: Optional[str] = None
    locales: List[Local] = []
    model_config = ConfigDict(from_attributes=True)

# --- ESQUEMAS PARA ENTRADA DE DATOS (CREAR/ACTUALIZAR) ---

class UsuarioCreateBase(BaseModel):
    nombre_completo: str
    tipo_documento: str
    numero_documento: str
    email: EmailStr
    telefono: str
    password: str
    rol_id: int
    local_asignado_id: int
    sueldo_base: Optional[float] = None

class NegocioCreate(BaseModel):
    ruc: str
    razon_social: str
    nombre_comercial: str
    marca_origen: str = 'metraes'
    dueño: UsuarioCreateBase # Se anida el esquema base para la creación del dueño

class NegocioUpdate(BaseModel):
    nombre_comercial: str
    modo_cobro: str
    tema_id: int
    logo_url: Optional[str] = None

class LocalCreate(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    telefono_contacto: Optional[str] = None

class LocalUpdate(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    telefono_contacto: Optional[str] = None

class MetodoPagoCreate(BaseModel):
    nombre_metodo: str
    datos_adicionales: Optional[dict] = None

# --- ESQUEMAS PARA AUTENTICACIÓN Y SEGURIDAD ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    numero_documento: Optional[str] = None

class UsuarioChangePassword(BaseModel):
    password_actual: str
    password_nuevo: str
    password_nuevo_confirmacion: str

class PasswordRecoveryRequest(BaseModel):
    tipo_documento: str
    numero_documento: str

class PasswordReset(BaseModel):
    token: str
    tipo_documento: str
    numero_documento: str
    nuevo_password: str


class ProveedorBase(BaseModel):
    ruc: str
    razon_social: str
    nombre_contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None

class ProveedorCreate(ProveedorBase):
    pass

class Proveedor(ProveedorBase):
    id: int
    negocio_id: int
    model_config = ConfigDict(from_attributes=True)