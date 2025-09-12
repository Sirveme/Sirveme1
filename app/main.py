from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.core.middleware import brand_middleware
from app.core.config import settings

# --- IMPORTACIÓN DE ROUTERS ---
from app.api.v1 import (
    rutas_auth,
    rutas_api_publica,
    rutas_gestion,
    rutas_kds,
    rutas_panel,
    rutas_publicas,
    rutas_superadmin,
    rutas_usuarios,
    rutas_web
)

app = FastAPI(title=settings.PROJECT_NAME)

# --- MIDDLEWARE ---
app.middleware("http")(brand_middleware)

# --- MONTAJE DE ARCHIVOS ESTÁTICOS ---
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- INCLUSIÓN DE ROUTERS DE API (con prefijo /api/v1) ---
# Todos los endpoints que devuelven JSON deben ir aquí.
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(rutas_api_publica.router, tags=["Público API"])
api_router.include_router(rutas_auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(rutas_gestion.router, tags=["Panel de Gestión"])
api_router.include_router(rutas_panel.router, tags=["Panel API"])
api_router.include_router(rutas_superadmin.router, tags=["Super Admin API"])
api_router.include_router(rutas_usuarios.router, tags=["Usuarios"])
app.include_router(api_router)


# --- INCLUSIÓN DE ROUTERS WEB (devuelven HTML, sin prefijo de API) ---
# Estas rutas deben ir DESPUÉS de las de la API para evitar conflictos.
app.include_router(rutas_web.router, tags=["Panel Web"])
app.include_router(rutas_kds.router, tags=["KDS WebSockets"]) # WebSockets tampoco llevan prefijo de API
app.include_router(rutas_publicas.router, tags=["Público Web"])


@app.get("/")
def read_root():
    return RedirectResponse(url="/home") # Redirigir la raíz a la página de inicio
