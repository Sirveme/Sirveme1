from fastapi import FastAPI
from app.core.middleware import brand_middleware
from fastapi.staticfiles import StaticFiles # <--- NUEVA IMPORTACIÓN
from app.core.config import settings
from app.api.v1 import rutas_usuarios, rutas_auth, rutas_web, rutas_panel, rutas_publicas, rutas_api_publica
from app.api.v1 import rutas_kds
from app.api.v1 import rutas_superadmin
from app.api.v1 import rutas_gestion

app = FastAPI(title=settings.PROJECT_NAME)
app.middleware("http")(brand_middleware)

# --- NUEVA CONFIGURACIÓN ---
# Monta la carpeta 'static' para que FastAPI pueda servir archivos CSS, JS, e imágenes
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configura el motor de plantillas Jinja2 para que busque plantillas en la carpeta 'templates'

# --- FIN NUEVA CONFIGURACIÓN ---

# INCLUYE EL ROUTER EN LA APLICACIÓN PRINCIPAL
app.include_router(rutas_web.router, tags=["Panel Web"])
app.include_router(rutas_publicas.router, tags=["Público Web"])
app.include_router(rutas_panel.router, prefix="/api/v1", tags=["Panel API"])
app.include_router(rutas_gestion.router, prefix="/api/v1", tags=["Panel de Gestión"])

# Routers con prefijo /api/v1
app.include_router(rutas_api_publica.router, prefix="/api/v1", tags=["Público API"]) # <-- CON PREFIJO
app.include_router(rutas_auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(rutas_usuarios.router, prefix="/api/v1", tags=["Usuarios"])
# El router del Super-Admin también es una API, debe tener el prefijo.
app.include_router(rutas_superadmin.router, prefix="/api/v1", tags=["Super Admin API"])

# El router del KDS no lleva prefijo /api/v1 para que la URL sea más simple (ej: /ws/kds/1)
app.include_router(rutas_kds.router, tags=["KDS WebSockets"])



@app.get("/")
def read_root():
    return {"message": "Bienvenido a " + settings.PROJECT_NAME}


