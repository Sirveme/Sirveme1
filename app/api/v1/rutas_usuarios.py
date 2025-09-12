from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError, jwt

# Importaciones estandarizadas
from app.db.conexion import SessionLocal
from app.db.modelos.modelos_core import Usuario
from app.esquemas import esquemas_core
from app.core.config import settings
from app.servicios import servicio_usuario

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DEPENDENCIA DE SEGURIDAD RECONSTRUIDA ---
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Intenta obtener el token de la cookie primero (para cargas de página)
    token = request.cookies.get("access_token")
    if token:
        # La cookie incluye "Bearer ", lo eliminamos
        token = token.split("Bearer ")[-1]

    # Si no hay cookie, intenta obtenerlo de la cabecera Authorization (para llamadas de API)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[-1]
    
    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        numero_documento: str = payload.get("sub")
        if numero_documento is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    usuario = db.query(Usuario).filter(Usuario.numero_documento == numero_documento).first()
    if usuario is None:
        raise credentials_exception
    return usuario


@router.get("/usuarios", response_model=List[esquemas_core.Usuario])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una lista de usuarios. Requiere autenticación.
    """
    if current_user.rol.nombre != 'SuperUsuario': # Ejemplo de protección por rol
        raise HTTPException(status_code=403, detail="No tienes permiso para ver todos los usuarios.")
    
    users = servicio_usuario.get_users(db, skip=skip, limit=limit)
    return users