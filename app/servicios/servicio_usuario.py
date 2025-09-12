# app/servicios/servicio_usuario.py
import secrets
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.modelos import modelos_core
from app.esquemas import esquemas_core
from app.core.seguridad import verificar_password, hashear_password
from app.core import seguridad

def authenticate_user(db: Session, numero_documento: str, password_plano: str):
    # Busca al usuario por su número de documento
    usuario = db.query(modelos_core.Usuario).filter(modelos_core.Usuario.numero_documento == numero_documento).first()
    if not usuario:
        return False
    # Verifica si la contraseña coincide
    if not seguridad.verificar_password(password_plano, usuario.password_hashed):
        return False
    return usuario

def get_usuario_por_numero_documento(db: Session, numero_documento: str) -> modelos_core.Usuario:
    """Busca un usuario por su número de documento."""
    return db.query(modelos_core.Usuario).filter(modelos_core.Usuario.numero_documento == numero_documento).first()

def crear_usuario(db: Session, usuario: esquemas_core.UsuarioCreateBase) -> modelos_core.Usuario:
    """Crea un nuevo usuario en la base de datos."""
    password_hasheado = hashear_password(usuario.password)
    db_usuario = modelos_core.Usuario(
        tipo_documento=usuario.tipo_documento,
        numero_documento=usuario.numero_documento,
        nombre_completo=usuario.nombre_completo,
        telefono=usuario.telefono,
        email=usuario.email,
        password_hashed=password_hasheado,
        rol_id=usuario.rol_id,
        negocio_id=usuario.negocio_id,
        activo=usuario.activo
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def cambiar_password_usuario(db: Session, *, usuario: modelos_core.Usuario, passwords: esquemas_core.UsuarioChangePassword) -> bool:
    """
    Cambia la contraseña de un usuario después de verificar la actual.
    Devuelve True si el cambio fue exitoso, False en caso contrario.
    """
    # 1. Verificar que la nueva contraseña y su confirmación coincidan
    if passwords.password_nuevo != passwords.password_nuevo_confirmacion:
        return False # O podríamos lanzar una excepción específica

    # 2. Verificar que la contraseña actual sea correcta
    if not verificar_password(passwords.password_actual, usuario.password_hashed):
        return False # O podríamos lanzar una excepción

    # 3. Hashear la nueva contraseña y actualizarla en el modelo
    nuevo_password_hasheado = hashear_password(passwords.password_nuevo)
    usuario.password_hashed = nuevo_password_hasheado

    # 4. Guardar los cambios en la base de datos
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return True


def get_usuario_por_email(db: Session, email: str) -> modelos_core.Usuario:
    """
    Busca un usuario por su email.
    """
    return db.query(modelos_core.Usuario).filter(modelos_core.Usuario.email == email).first()

def solicitar_reseteo_password(db: Session, tipo_documento: str, numero_documento: str) -> Optional[str]:
    """Genera un código de reseteo para un usuario y lo guarda en la BD."""
    usuario = db.query(modelos_core.Usuario).filter(
        modelos_core.Usuario.tipo_documento == tipo_documento,
        modelos_core.Usuario.numero_documento == numero_documento
    ).first()

    if not usuario:
        return None # No revelar si el usuario existe

    # Generar un código numérico seguro de 6 dígitos
    codigo = str(secrets.randbelow(1_000_000)).zfill(6)
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=10) # Código válido por 10 min

    usuario.reset_password_token = codigo
    usuario.reset_password_token_expires = expire_time
    db.add(usuario)
    db.commit()
    
    # En un futuro, aquí se enviaría el código por WhatsApp al usuario.telefono
    # send_whatsapp_code(usuario.telefono, codigo)

    return codigo # Devolvemos el código para poder probar

def resetear_password(db: Session, *, data: esquemas_core.PasswordReset) -> bool:
    """Resetea la contraseña de un usuario usando un código válido."""
    usuario = db.query(modelos_core.Usuario).filter(
        modelos_core.Usuario.tipo_documento == data.tipo_documento,
        modelos_core.Usuario.numero_documento == data.numero_documento,
        modelos_core.Usuario.reset_password_token == data.token
    ).first()

    if not usuario or usuario.reset_password_token_expires < datetime.now(timezone.utc):
        return False

    nuevo_password_hasheado = hashear_password(data.nuevo_password)
    usuario.password_hashed = nuevo_password_hasheado
    
    usuario.reset_password_token = None
    usuario.reset_password_token_expires = None
    db.add(usuario)
    db.commit()

    return True