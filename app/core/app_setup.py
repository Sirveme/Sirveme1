from fastapi import Request
from fastapi.templating import Jinja2Templates

# 1. Definimos la instancia de Jinja2Templates directamente
#    Le decimos que el directorio de plantillas es 'app/templates'.
#    FastAPI es lo suficientemente inteligente como para manejar subcarpetas
#    cuando se usa de esta manera.
templates = Jinja2Templates(directory="app/templates")

# 2. Definimos una función de middleware simple para la lógica Multi-Marca
async def brand_middleware(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0]
    
    if "sirveme1.com" in host or "127.0.0.1" in host or "localhost" in host: # Asumimos sirveme1 como el por defecto para desarrollo
        request.state.brand_config = {
            "brand_name": "Sirveme1",
            "logo_url": "/static/img/sirveme1_logo.png",
            "css_file": "/static/css/sirveme1_theme.css"
        }
    elif "metraes.com" in host:
        request.state.brand_config = {
            "brand_name": "Metraes",
            "logo_url": "/static/img/metraes_logo.png",
            "css_file": "/static/css/metraes_theme.css"
        }
    else: # Fallback por si no coincide
        request.state.brand_config = {
            "brand_name": "Sirveme1",
            "logo_url": "/static/img/sirveme1_logo.png",
            "css_file": "/static/css/sirveme1_theme.css"
        }
        
    response = await call_next(request)
    return response