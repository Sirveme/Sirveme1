from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Importaciones estandarizadas
from app.db.conexion import SessionLocal
from app.db.modelos import modelos_core
from app.esquemas import esquemas_core
from app.api.v1.rutas_usuarios import get_current_user
from app.core.seguridad import hashear_password

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Dependencia de Seguridad Específica para Super-Admin ---
def get_super_usuario(current_user: modelos_core.Usuario = Depends(get_current_user)):
    if not current_user.rol or current_user.rol.nombre != 'SuperUsuario':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de Super Administrador."
        )
    return current_user

# --- Endpoints del Super-Admin ---

@router.get("/superadmin/negocios", response_model=List[esquemas_core.Negocio])
def get_lista_negocios(
    db: Session = Depends(get_db),
    super_user: modelos_core.Usuario = Depends(get_super_usuario)
):
    """
    Devuelve una lista de todos los negocios registrados en el sistema.
    """
    negocios = db.query(modelos_core.Negocio).order_by(modelos_core.Negocio.id.desc()).all()
    return negocios

@router.post("/superadmin/negocios", response_model=esquemas_core.Negocio, status_code=status.HTTP_201_CREATED)
def crear_negocio_y_dueño(
    negocio_in: esquemas_core.NegocioCreate,
    db: Session = Depends(get_db),
    super_user: modelos_core.Usuario = Depends(get_super_usuario)
):
    """
    Crea un nuevo Negocio y su primer usuario 'Dueño'.
    Solo accesible por un SuperUsuario.
    """
    # Verificar si el RUC o el email del dueño ya existen
    db_negocio = db.query(modelos_core.Negocio).filter(modelos_core.Negocio.ruc == negocio_in.ruc).first()
    if db_negocio:
        raise HTTPException(status_code=400, detail="El RUC ya está registrado.")
    
    db_usuario = db.query(modelos_core.Usuario).filter(modelos_core.Usuario.email == negocio_in.dueño.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email del dueño ya está en uso.")

    # Obtener el rol de "Dueño"
    rol_dueño = db.query(modelos_core.Rol).filter(modelos_core.Rol.nombre == 'Dueño').first()
    if not rol_dueño:
        raise HTTPException(status_code=500, detail="El rol 'Dueño' no está configurado en el sistema.")

    # Crear el nuevo negocio
    nuevo_negocio = modelos_core.Negocio(
        ruc=negocio_in.ruc,
        razon_social=negocio_in.razon_social,
        nombre_comercial=negocio_in.nombre_comercial,
        marca_origen=negocio_in.marca_origen
    )
    db.add(nuevo_negocio)
    db.flush() # Para obtener el ID del nuevo negocio antes del commit

    # Crear el usuario dueño asociado
    nuevo_dueño = modelos_core.Usuario(
        nombre_completo=negocio_in.dueño.nombre_completo,
        tipo_documento=negocio_in.dueño.tipo_documento,
        numero_documento=negocio_in.dueño.numero_documento,
        email=negocio_in.dueño.email,
        telefono=negocio_in.dueño.telefono,
        password_hashed=hashear_password(negocio_in.dueño.password),
        rol_id=rol_dueño.id,
        negocio_id=nuevo_negocio.id # <-- Asociación clave
    )
    db.add(nuevo_dueño)
    
    db.commit()
    db.refresh(nuevo_negocio)
    
    return nuevo_negocio