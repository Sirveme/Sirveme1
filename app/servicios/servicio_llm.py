import google.generativeai as genai
import json
from typing import Dict, Any, List

from app.core.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


def procesar_orden_con_llm(menu_simple: List[Dict[str, Any]], texto_usuario: str) -> Dict[str, Any]:
    # Convertimos la lista de menú a un string simple para el prompt
    menu_texto = "\n".join([f"- ID: {item['id']}, Nombre: '{item['nombre']}', Alias: {item.get('alias', 'N/A')}" for item in menu_simple])

    prompt = f"""
    Analiza la orden de un cliente y conviértela a JSON. Eres un experto en reconocer productos de un menú.

    ### MENÚ DISPONIBLE:
    {menu_texto}

    ### ORDEN DEL CLIENTE:
    "{texto_usuario}"

    ### TUS REGLAS:
    1.  **Determina la INTENCIÓN:** 'ADD_ITEMS', 'MODIFY_QUANTITY', 'REMOVE_ITEMS', 'RESET_ORDER', o 'NOT_FOUND'.
    2.  **Extrae ENTIDADES:** Identifica los productos por su Nombre o Alias. Extrae su ID y la CANTIDAD numérica exacta. Si no hay cantidad, es 1.
    3.  **Para "REMOVE_ITEMS" sin número, la cantidad es 999.**
    4.  **Responde ÚNICAMENTE con el JSON.**

    ### FORMATO JSON:
    {{
      "intent": "...",
      "entities": [
        {{ "product_id": <ID>, "quantity": <CANTIDAD> }}
      ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        json_response_str = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_response_str)
    except Exception as e:
        print(f"[ERROR en LLM]: {e}")
        return {"intent": "UNKNOWN", "entities": []}