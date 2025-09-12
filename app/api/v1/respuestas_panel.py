# app/api/v1/respuestas_panel.py
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.core.app_setup import templates

def PanelBaseResponse(request: Request, current_user, template_name: str, context: dict) -> HTMLResponse:
    """
    Función que renderiza una página completa del panel.
    Acepta un fragmento de HTML (template_name) y lo inyecta en la plantilla base.
    """
    brand_config = request.state.brand_config
    user_permissions = {p.codigo for p in current_user.rol.permisos}
    
    # Contexto global para la plantilla base
    global_context = {
        "request": request,
        "current_user": current_user,
        "brand_config": brand_config,
        "user_permissions": user_permissions,
        "content_template": template_name, # La plantilla a inyectar en el main content
        **context
    }
    
    return templates.TemplateResponse("panel/panel_base.html", global_context)