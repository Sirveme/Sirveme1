# Endpoints para autenticación (login, tokens)
# app/api/v1/rutas_auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

# Importaciones estandarizadas y corregidas
from app.db.conexion import SessionLocal
from app.db.modelos import modelos_core
from app.esquemas import esquemas_auth, esquemas_core
from app.servicios.servicio_usuario import authenticate_user # <-- Importación correcta
from app.core.seguridad import crear_access_token, ACCESS_TOKEN_EXPIRE_MINUTES # <-- Importaciones correctas

from app.api.v1.rutas_usuarios import get_current_user
from app.servicios import servicio_usuario
from app.core import seguridad
from app.core.config import settings
from sqlalchemy.orm import Session


router = APIRouter()

# Función de dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/token", response_model=esquemas_auth.Token)
def login(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    usuario = authenticate_user(db=db, numero_documento=form_data.username, password_plano=form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Número de documento o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crear_access_token(
        data={"sub": usuario.numero_documento}, expires_delta=access_token_expires
    )

    # Creamos una respuesta JSON explícita para devolver el token en el cuerpo
    # La cookie se mantiene por ahora para compatibilidad, pero el frontend usará el token del cuerpo.
    token_json = {"access_token": access_token, "token_type": "bearer"}
    response = JSONResponse(content=token_json)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        expires=access_token_expires.total_seconds()
    )
    return response


@router.post("/password-recovery", response_model=dict)
def recover_password(data: esquemas_core.PasswordRecoveryRequest, db: Session = Depends(get_db)):
    codigo = servicio_usuario.solicitar_reseteo_password(
        db=db,
        tipo_documento=data.tipo_documento,
        numero_documento=data.numero_documento
    )
    # Para pruebas, devolvemos el código. En producción, solo el mensaje.
    if codigo:
        return {"msg": "Código de recuperación generado.", "codigo_prueba": codigo}
    return {"msg": "Si los datos son correctos, se ha enviado un código de recuperación."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    data: esquemas_core.PasswordReset, 
    db: Session = Depends(get_db)
):
    """
    Finaliza el proceso de reseteo de contraseña usando el token/código.
    """
    # Ahora pasamos el objeto 'data' completo directamente al servicio.
    exito = servicio_usuario.resetear_password(db=db, data=data) 

    if not exito:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código es inválido, ha expirado o los datos no coinciden.",
        )
    
    return

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"msg": "Logout exitoso"}


@router.get("/users/me", response_model=esquemas_core.Usuario)
def read_users_me(current_user: modelos_core.Usuario = Depends(get_current_user)):
    """
    Endpoint protegido que devuelve los datos del usuario actual.
    Sirve para verificar si el token JWT es válido.
    """
    return current_user


@router.get("/users/me", response_model=esquemas_core.Usuario)
def read_users_me(current_user: modelos_core.Usuario = Depends(get_current_user)):
    """
    Endpoint protegido que devuelve los datos del usuario actual.
    Sirve para verificar si el token JWT es válido.
    """
    return current_user