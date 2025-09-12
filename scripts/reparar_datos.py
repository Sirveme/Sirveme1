import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.db.modelos.modelos_core import Producto, GrupoModificador

def reparar_asociaciones():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    print("--- Iniciando script de reparación de asociaciones ---")
    
    try:
        # --- DEFINIR LAS REGLAS DE NEGOCIO CORRECTAS AQUÍ ---
        # Formato: { 'Nombre del Producto': ['Grupo Modificador Correcto 1', 'Grupo Correcto 2'] }
        
        reglas_correctas = {
            'Papa Rellena': ['Cremas'],
            'Helado Artesanal': ['Sabores de Helado']
            # Añade aquí más reglas para otros productos
        }

        # --- OBTENER TODOS LOS ELEMENTOS DE LA BD ---
        todos_los_productos = db.query(Producto).options(joinedload(Producto.grupos_modificadores)).all()
        todos_los_grupos = db.query(GrupoModificador).all()
        
        mapa_grupos = {grupo.nombre: grupo for grupo in todos_los_grupos}

        # --- APLICAR LAS REGLAS ---
        for prod in todos_los_productos:
            if prod.nombre in reglas_correctas:
                print(f"Verificando producto: '{prod.nombre}'...")
                
                grupos_correctos_nombres = reglas_correctas[prod.nombre]
                grupos_correctos_obj = {mapa_grupos[nombre] for nombre in grupos_correctos_nombres if nombre in mapa_grupos}
                
                grupos_actuales_obj = set(prod.grupos_modificadores)
                
                # 1. Eliminar asociaciones incorrectas
                grupos_a_eliminar = grupos_actuales_obj - grupos_correctos_obj
                for grupo_a_eliminar in grupos_a_eliminar:
                    prod.grupos_modificadores.remove(grupo_a_eliminar)
                    print(f"  - [CORREGIDO] Se eliminó asociación incorrecta con '{grupo_a_eliminar.nombre}'.")

                # 2. Añadir asociaciones correctas que falten
                grupos_a_anadir = grupos_correctos_obj - grupos_actuales_obj
                for grupo_a_anadir in grupos_a_anadir:
                    prod.grupos_modificadores.append(grupo_a_anadir)
                    print(f"  - [CORREGIDO] Se añadió la asociación correcta con '{grupo_a_anadir.nombre}'.")

        db.commit()
        print("--- Reparación finalizada con éxito. ---")
        
    finally:
        db.close()

if __name__ == "__main__":
    reparar_asociaciones()