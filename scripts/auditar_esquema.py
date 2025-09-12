import sys
import os
from sqlalchemy import create_engine, inspect

# Añadir la ruta del proyecto para que podamos importar la configuración
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def auditar_esquema_db():
    """
    Se conecta a la base de datos definida en la configuración y genera un
    informe detallado del esquema (tablas y columnas).
    """
    print("--- Iniciando Auditoría de Esquema de Base de Datos ---")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        schemas = inspector.get_schema_names()
        
        print(f"\nEsquemas encontrados: {schemas}\n")
        
        for schema in schemas:
            if schema in ['information_schema', 'pg_catalog', 'pg_toast']:
                continue

            print(f"--- TABLAS EN EL ESQUEMA: '{schema}' ---")
            tables = inspector.get_table_names(schema=schema)
            
            if not tables:
                print("   (No hay tablas en este esquema)")
                continue

            for table_name in sorted(tables):
                print(f"\n-> Tabla: {table_name}")
                
                # Obtener columnas
                columns = inspector.get_columns(table_name, schema=schema)
                for column in columns:
                    col_info = f"   - {column['name']} ({str(column['type'])})"
                    if column.get('nullable') == False:
                        col_info += ", NOT NULL"
                    if column.get('primary_key') == 1:
                        col_info += ", PRIMARY KEY"
                    print(col_info)
                
                # Obtener claves foráneas
                foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
                if foreign_keys:
                    print("     Foreign Keys:")
                    for fk in foreign_keys:
                        constrained_cols = ", ".join(fk['constrained_columns'])
                        referred_table = fk['referred_table']
                        referred_cols = ", ".join(fk['referred_columns'])
                        print(f"       - ({constrained_cols}) -> {referred_table}({referred_cols})")

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error durante la auditoría: {e}")
        print("        Asegúrate de que la variable DATABASE_URL en tu archivo .env sea correcta.")
        return

    print("\n--- Auditoría de Esquema Finalizada ---")

if __name__ == "__main__":
    auditar_esquema_db()