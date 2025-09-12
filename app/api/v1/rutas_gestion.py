from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.seguridad import hashear_password

# Importaciones estandarizadas
from app.db.conexion import SessionLocal
from app.db.modelos import modelos_core
from app.esquemas import esquemas_core
from app.api.v1.rutas_usuarios import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ENDPOINTS PARA GESTIÓN DE PERSONAL ---
@router.get("/panel/personal", response_model=List[esquemas_core.Usuario])
def get_personal(
    db: Session = Depends(get_db),
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    """Obtiene todo el personal del negocio del usuario actual."""
    personal = db.query(modelos_core.Usuario).filter(
        modelos_core.Usuario.negocio_id == current_user.negocio_id
    ).all()
    return personal

# (Aquí irían las rutas POST, PUT, DELETE para personal)

# --- ENDPOINTS PARA GESTIÓN DE PROVEEDORES ---
@router.get("/panel/proveedores", response_model=List[esquemas_core.Proveedor])
def get_proveedores(
    db: Session = Depends(get_db),
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    """Obtiene todos los proveedores del negocio del usuario actual."""
    proveedores = db.query(modelos_core.Proveedor).filter(
        modelos_core.Proveedor.negocio_id == current_user.negocio_id
    ).all()
    return proveedores

@router.post("/panel/proveedores", response_model=esquemas_core.Proveedor, status_code=status.HTTP_201_CREATED)
def create_proveedor(
    proveedor_in: esquemas_core.ProveedorCreate,
    db: Session = Depends(get_db),
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    """Crea un nuevo proveedor para el negocio del usuario actual."""
    nuevo_proveedor = modelos_core.Proveedor(
        **proveedor_in.model_dump(),
        negocio_id=current_user.negocio_id
    )
    db.add(nuevo_proveedor)
    db.commit()
    db.refresh(nuevo_proveedor)
    return nuevo_proveedor

# (Aquí irían las rutas PUT, DELETE para proveedores)



# --- ENDPOINTS PARA GESTIÓN DE ROLES ---
@router.get("/gestion/roles", response_model=List[esquemas_core.Rol])
def get_roles_para_asignar(
    db: Session = Depends(get_db),
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    roles = db.query(modelos_core.Rol).filter(modelos_core.Rol.nombre.not_in(['SuperUsuario', 'Dueño'])).all()
    return roles

@router.get("/gestion/locales", response_model=List[esquemas_core.Local])
def get_locales_del_negocio(
    db: Session = Depends(get_db),
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    locales = db.query(modelos_core.Local).filter(modelos_core.Local.negocio_id == current_user.negocio_id).all()
    return locales


# --- ENDPOINTS PARA GESTIÓN DE PERSONAL ---
@router.get("/gestion/personal", response_model=List[esquemas_core.Usuario])
def get_personal_del_negocio(
    db: Session = Depends(get_db),
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    personal = db.query(modelos_core.Usuario).filter(
        modelos_core.Usuario.negocio_id == current_user.negocio_id
    ).all()
    return personal

@router.post("/gestion/personal", response_model=esquemas_core.Usuario, status_code=status.HTTP_201_CREATED)
def create_empleado(
    empleado_in: esquemas_core.UsuarioCreateBase,
    db: Session = Depends(get_db),
    current_user: modelos_core.Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo usuario (empleado) para el negocio del usuario 'Dueño' actual.
    """
    # Verificación de permisos (solo el Dueño puede crear personal)
    if current_user.rol.nombre != 'Dueño':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para crear empleados.")

    # Verificar si el documento o el email ya existen en el sistema
    db_usuario_doc = db.query(modelos_core.Usuario).filter(modelos_core.Usuario.numero_documento == empleado_in.numero_documento).first()
    if db_usuario_doc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El número de documento ya está registrado.")
    
    db_usuario_email = db.query(modelos_core.Usuario).filter(modelos_core.Usuario.email == empleado_in.email).first()
    if db_usuario_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está en uso.")

    # Crear el nuevo objeto Usuario
    nuevo_empleado = modelos_core.Usuario(
        nombre_completo=empleado_in.nombre_completo,
        tipo_documento=empleado_in.tipo_documento,
        numero_documento=empleado_in.numero_documento,
        email=empleado_in.email,
        telefono=empleado_in.telefono,
        password_hashed=hashear_password(empleado_in.password),
        rol_id=empleado_in.rol_id,
        negocio_id=current_user.negocio_id  # Se asigna al negocio del Dueño
    )

    db.add(nuevo_empleado)
    db.commit()
    db.refresh(nuevo_empleado)
    
    return nuevo_empleado