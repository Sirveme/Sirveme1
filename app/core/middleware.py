# app/core/middleware.py
from fastapi import Request

# Define la configuración para cada marca. En un futuro, esto podría venir de un archivo .json o de la BD.
BRAND_CONFIG = {
    "metraes.com": {
        "brand_name": "Metraes",
        "css_file": "/static/css/metraes.css",
        "logo_url": "/static/img/metraes_logo.webp", # Asegúrate de tener estas imágenes de prueba
        "lang_file": "metraes_es.json"
    },
    "sirveme1.com": {
        "brand_name": "Sirveme1",
        "css_file": "/static/css/sirveme1.css",
        "logo_url": "/static/img/sirveme1_logo.webp",
        "lang_file": "sirveme1_es.json"
    },
    # Un 'default' para cuando se accede por localhost
    "default": {
        "brand_name": "Metraes (Local)",
        "css_file": "/static/css/metraes.css",
        "logo_url": "/static/img/metraes_logo.webp",
        "lang_file": "metraes_es.json"
    }
}

async def brand_middleware(request: Request, call_next):
    """
    Middleware para detectar el dominio y adjuntar la configuración de marca a la petición.
    """
    # Obtenemos el host desde las cabeceras. En producción, esto podría ser 'metraes.com'.
    # Para pruebas locales, será '127.0.0.1' o 'localhost'.
    host = request.headers.get("host", "").split(":")[0] 

    # Seleccionamos la configuración de marca. Si el host no está en nuestro config, usamos 'default'.
    config = BRAND_CONFIG.get(host, BRAND_CONFIG["default"])
    
    # Adjuntamos la configuración al 'state' de la petición.
    # Esto hace que 'request.state.brand_config' esté disponible en todos los endpoints.
    request.state.brand_config = config
    
    response = await call_next(request)
    return response