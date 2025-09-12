from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Configura el contexto de passlib para usar bcrypt como el algoritmo de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- ¡CONSTANTE AÑADIDA Y CORREGIDA! ---
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 horas

def verificar_password(password_plano: str, password_hashed: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con una hasheada."""
    return pwd_context.verify(password_plano, password_hashed)

def hashear_password(password: str) -> str:
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password)


def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Crea un nuevo token de acceso JWT.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # --- ¡LÓGICA CORREGIDA PARA USAR LA CONSTANTE! ---
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt