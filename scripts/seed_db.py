import sys
import os
from sqlalchemy.orm import Session
from decimal import Decimal

# Añadir la ruta del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importaciones explícitas y ordenadas
from app.db.conexion import SessionLocal
from app.db.modelos import modelos_core, modelos_operativos, modelos_configuracion
from app.core.seguridad import hashear_password

def seed_database():
    print("Iniciando el proceso de siembra de la base de datos...")
    db: Session = SessionLocal()
    try:
        # --- 1. CREAR ROLES ---
        if db.query(modelos_core.Rol).count() == 0:
            print("Creando roles iniciales...")
            ROLES_A_CREAR = [
                {'id': 1, 'nombre': 'Dueño', 'descripcion': 'Acceso total al negocio propio'},
                {'id': 11, 'nombre': 'SuperUsuario', 'descripcion': 'Dueño del Sistema'},
                {'id': 6, 'nombre': 'Mozo', 'descripcion': 'Personal de servicio en el salón'},
                {'id': 7, 'nombre': 'Cajero', 'descripcion': 'Personal de caja'},
                {'id': 8, 'nombre': 'Cocinero', 'descripcion': 'Personal de cocina'},
                {'id': 9, 'nombre': 'Bartender', 'descripcion': 'Personal de barra y cockteles'}
            ]
            for rol_data in ROLES_A_CREAR:
                db.add(modelos_core.Rol(**rol_data))
            db.commit()
            print(f"-> {len(ROLES_A_CREAR)} roles creados.")
        else:
            print("Roles ya existen. Omitiendo.")

        # --- 2. CREAR TEMAS DE DEMOSTRACIÓN ---
        if db.query(modelos_configuracion.Tema).count() == 0:
            print("Creando temas de demostración...")
            tema_disco = modelos_configuracion.Tema(nombre="Neón Discoteca", descripcion="Ideal para bares y discotecas con ambiente oscuro.")
            tema_resto = modelos_configuracion.Tema(nombre="Clásico Restaurante", descripcion="Un tema elegante y sobrio para restaurantes.")
            db.add_all([tema_disco, tema_resto])
            db.commit()
            print("-> Temas 'Neón Discoteca' y 'Clásico Restaurante' creados.")
        else:
            print("Temas ya existen. Omitiendo.")

        # --- 3. CREAR NEGOCIOS DE PRUEBA ---
        negocio_resto = db.query(modelos_core.Negocio).filter_by(ruc='11111111111').first()
        if not negocio_resto:
            print("Creando negocio 'Sabor Criollo' (Restaurante)...")
            tema_resto_id = db.query(modelos_configuracion.Tema.id).filter_by(nombre="Clásico Restaurante").scalar()
            negocio_resto = modelos_core.Negocio(
                ruc='11111111111', razon_social='Sabor Criollo SAC',
                nombre_comercial='Sabor Criollo', marca_origen='metraes',
                modo_cobro='POSTPAGO', tema_id=tema_resto_id
            )
            db.add(negocio_resto)

        negocio_disco = db.query(modelos_core.Negocio).filter_by(ruc='20111111111').first()
        if not negocio_disco:
            print("Creando negocio 'Nieves' (Discoteca)...")
            tema_disco_id = db.query(modelos_configuracion.Tema.id).filter_by(nombre="Neón Discoteca").scalar()
            negocio_disco = modelos_core.Negocio(
                ruc='20111111111', razon_social='Discoteca Nieves EIRL',
                nombre_comercial='Nieves', marca_origen='sirveme1',
                modo_cobro='PREPAGO', tema_id=tema_disco_id
            )
            db.add(negocio_disco)

        db.commit()
        # Volver a cargar las variables para asegurar que tenemos los objetos completos
        negocio_resto = db.query(modelos_core.Negocio).filter_by(ruc='11111111111').one()
        negocio_disco = db.query(modelos_core.Negocio).filter_by(ruc='20111111111').one()
        print("-> Negocios de demostración creados o verificados.")

        # --- 4. CREAR USUARIOS DEL SISTEMA ---
        if db.query(modelos_core.Usuario).count() == 0:
            print("Creando usuarios del sistema...")
            rol_dueño = db.query(modelos_core.Rol).filter_by(nombre='Dueño').one()
            rol_super = db.query(modelos_core.Rol).filter_by(nombre='SuperUsuario').one()
            
            db.add(modelos_core.Usuario(nombre_completo='Dueño Sabor Criollo', tipo_documento='DNI', numero_documento='12345678', telefono='999888777', email='dueño_resto@test.com', password_hashed=hashear_password('clave123'), negocio_id=negocio_resto.id, rol_id=rol_dueño.id))
            db.add(modelos_core.Usuario(nombre_completo='Dueña Nieves', tipo_documento='DNI', numero_documento='87654321', telefono='988777666', email='dueña_disco@test.com', password_hashed=hashear_password('clave123'), negocio_id=negocio_disco.id, rol_id=rol_dueño.id))
            db.add(modelos_core.Usuario(nombre_completo='Super Administrador', tipo_documento='DNI', numero_documento='00000000', telefono='900000000', email='superadmin@sistema.com', password_hashed=hashear_password('superadmin'), rol_id=rol_super.id, negocio_id=None))
            
            db.commit()
            print("-> Usuarios creados para ambos negocios y SuperAdmin.")
        else:
            print("Usuarios ya existen. Omitiendo.")

        # --- 5. CREAR INFRAESTRUCTURA FÍSICA ---
        if db.query(modelos_core.Mesa).count() == 0:
            print("Creando infraestructura (Centros, Locales, Zonas, Mesas)...")
            
            # Infraestructura para Sabor Criollo
            cocina_resto = modelos_operativos.CentroProduccion(nombre='Cocina', negocio_id=negocio_resto.id)
            barra_resto = modelos_operativos.CentroProduccion(nombre='Barra', negocio_id=negocio_resto.id)
            db.add_all([cocina_resto, barra_resto])
            local_resto = modelos_core.Local(nombre='Local Principal', direccion='Av. Criolla 123', negocio_id=negocio_resto.id)
            db.add(local_resto)
            db.flush()
            zona_resto = modelos_core.Zona(nombre='Salón Principal', local_id=local_resto.id)
            db.add(zona_resto)
            db.flush()
            db.add_all([
                modelos_core.Mesa(nombre_o_numero='Mesa 1', capacidad=4, zona_id=zona_resto.id),
                modelos_core.Mesa(nombre_o_numero='Mesa 2', capacidad=2, zona_id=zona_resto.id)
            ])
            
            # Infraestructura para Nieves
            barra_disco = modelos_operativos.CentroProduccion(nombre='Barra Principal', negocio_id=negocio_disco.id)
            caja_disco = modelos_operativos.CentroProduccion(nombre='Caja', negocio_id=negocio_disco.id)
            db.add_all([barra_disco, caja_disco])
            local_disco = modelos_core.Local(nombre='Local Sandía', direccion='Jr. Puno 456', negocio_id=negocio_disco.id)
            db.add(local_disco)
            db.flush()
            zona_vip_disco = modelos_core.Zona(nombre='Zona VIP', local_id=local_disco.id)
            db.add(zona_vip_disco)
            db.flush()
            db.add_all([
                modelos_core.Mesa(nombre_o_numero='Box 1', capacidad=8, zona_id=zona_vip_disco.id),
                modelos_core.Mesa(nombre_o_numero='Box 2', capacidad=8, zona_id=zona_vip_disco.id)
            ])
            
            db.commit()
            print("-> Infraestructura para ambos negocios creada.")
        else:
            print("Infraestructura ya existe. Omitiendo.")

        # --- 6. CREAR MENÚS DE DEMOSTRACIÓN (VERSIÓN ENRIQUECIDA Y COMPLETA) ---
        if db.query(modelos_core.Producto).count() == 0:
            print("Creando menús de demostración...")
            
            # --- MENÚ PARA "SABOR CRIOLLO" (RESTAURANTE) ---
            negocio_resto = db.query(modelos_core.Negocio).filter_by(ruc='11111111111').one()
            id_cocina_resto = db.query(modelos_operativos.CentroProduccion.id).filter_by(nombre='Cocina', negocio_id=negocio_resto.id).scalar()
            id_barra_resto = db.query(modelos_operativos.CentroProduccion.id).filter_by(nombre='Barra', negocio_id=negocio_resto.id).scalar()
            
            categorias_resto = {
                'entradas': modelos_core.Categoria(nombre='Entradas', negocio_id=negocio_resto.id),
                'principales': modelos_core.Categoria(nombre='Platos Principales', negocio_id=negocio_resto.id),
                'pizzas': modelos_core.Categoria(nombre='Pizzas', negocio_id=negocio_resto.id),
                'bebidas': modelos_core.Categoria(nombre='Bebidas', negocio_id=negocio_resto.id)
            }
            for cat in categorias_resto.values(): db.add(cat)
            db.flush()

            # Productos para Sabor Criollo
            db.add_all([
                modelos_core.Producto(nombre="Lomo Saltado", precio_base=Decimal('35.00'), categoria_id=categorias_resto['principales'].id, negocio_id=negocio_resto.id, centro_produccion_id=id_cocina_resto, tipo_producto="PLATO", tiene_variantes=False),
                modelos_core.Producto(nombre="Papa a la Huancaína", precio_base=Decimal('18.00'), categoria_id=categorias_resto['entradas'].id, negocio_id=negocio_resto.id, centro_produccion_id=id_cocina_resto, tipo_producto="PLATO", tiene_variantes=False),
                modelos_core.Producto(nombre="Inca Kola", precio_base=Decimal('5.00'), categoria_id=categorias_resto['bebidas'].id, negocio_id=negocio_resto.id, centro_produccion_id=id_barra_resto, tipo_producto="BEBIDA", tiene_variantes=False, alias="gaseosa"),
                modelos_core.Producto(nombre="Cerveza Cusqueña", precio_base=Decimal('10.00'), categoria_id=categorias_resto['bebidas'].id, negocio_id=negocio_resto.id, centro_produccion_id=id_barra_resto, tipo_producto="BEBIDA", tiene_variantes=False, alias="chela")
            ])
            
            pizza_americana = modelos_core.Producto(nombre="Pizza Americana", precio_base=Decimal('0.00'), categoria_id=categorias_resto['pizzas'].id, negocio_id=negocio_resto.id, centro_produccion_id=id_cocina_resto, tipo_producto="PLATO", tiene_variantes=True)
            db.add(pizza_americana)
            db.flush()
            db.add_all([modelos_core.VarianteProducto(producto_id=pizza_americana.id, nombre="Mediana", precio=Decimal('30.00')), modelos_core.VarianteProducto(producto_id=pizza_americana.id, nombre="Familiar", precio=Decimal('45.00'))])

            # --- MENÚ PARA "NIEVES" (DISCOTECA) ---
            negocio_disco = db.query(modelos_core.Negocio).filter_by(ruc='20111111111').one()
            id_barra_disco = db.query(modelos_operativos.CentroProduccion.id).filter_by(nombre='Barra Principal', negocio_id=negocio_disco.id).scalar()
            id_caja_disco = db.query(modelos_operativos.CentroProduccion.id).filter_by(nombre='Caja', negocio_id=negocio_disco.id).scalar()
            
            # Usamos tu lista completa de categorías
            categorias_disco = {
                'piqueos': modelos_core.Categoria(nombre='Piqueos', negocio_id=negocio_disco.id),
                'cervezas': modelos_core.Categoria(nombre='Cervezas', negocio_id=negocio_disco.id),
                'cockteles': modelos_core.Categoria(nombre='Cockteles', negocio_id=negocio_disco.id),
                'licores': modelos_core.Categoria(nombre='Licores', negocio_id=negocio_disco.id),
                'cigarrillos': modelos_core.Categoria(nombre='Cigarrillos', negocio_id=negocio_disco.id),
                'snacks': modelos_core.Categoria(nombre='Snacks', negocio_id=negocio_disco.id)
            }
            for cat in categorias_disco.values(): db.add(cat)
            db.flush()
            
            # Usamos y ampliamos tu lista de productos
            db.add_all([
                modelos_core.Producto(nombre="Alitas Buffalo", precio_base=Decimal('18.00'), categoria_id=categorias_disco['piqueos'].id, negocio_id=negocio_disco.id, centro_produccion_id=id_caja_disco, tipo_producto="PLATO"),
                modelos_core.Producto(nombre="Cerveza Pilsen", precio_base=Decimal('12.00'), categoria_id=categorias_disco['cervezas'].id, negocio_id=negocio_disco.id, centro_produccion_id=id_barra_disco, tipo_producto="BEBIDA"),
                modelos_core.Producto(nombre="Cerveza Corona", precio_base=Decimal('15.00'), categoria_id=categorias_disco['cervezas'].id, negocio_id=negocio_disco.id, centro_produccion_id=id_barra_disco, tipo_producto="BEBIDA"),
                modelos_core.Producto(nombre="Cuba Libre", precio_base=Decimal('18.00'), categoria_id=categorias_disco['cockteles'].id, negocio_id=negocio_disco.id, centro_produccion_id=id_barra_disco, tipo_producto="BEBIDA"),
                modelos_core.Producto(nombre="Chilcano de Pisco", precio_base=Decimal('16.00'), categoria_id=categorias_disco['cockteles'].id, negocio_id=negocio_disco.id, centro_produccion_id=id_barra_disco, tipo_producto="BEBIDA"),
                modelos_core.Producto(nombre="Cigarrillos Lucky Strike", precio_base=Decimal('20.00'), categoria_id=categorias_disco['cigarrillos'].id, negocio_id=negocio_disco.id, centro_produccion_id=id_caja_disco, tipo_producto="RETAIL"),
                modelos_core.Producto(nombre="Chiclets Trident", precio_base=Decimal('2.50'), categoria_id=categorias_disco['snacks'].id, negocio_id=negocio_disco.id, centro_produccion_id=id_caja_disco, tipo_producto="RETAIL")
            ])
            
            jw_black = modelos_core.Producto(nombre="Whisky JW Black Label", precio_base=Decimal('0.00'), categoria_id=categorias_disco['licores'].id, negocio_id=negocio_disco.id, centro_produccion_id=id_barra_disco, tipo_producto="BEBIDA", tiene_variantes=True)
            db.add(jw_black)
            db.flush()
            db.add_all([
                modelos_core.VarianteProducto(producto_id=jw_black.id, nombre="Botella", precio=Decimal('180.00')),
                modelos_core.VarianteProducto(producto_id=jw_black.id, nombre="Trago", precio=Decimal('35.00'))
            ])
            
            db.commit()
            print("-> Menús de demostración creados.")
        else:
            print("Menú ya existe. Omitiendo.")

        print("\n¡Proceso de siembra completado con éxito!")

    except Exception as e:
        print(f"\nOcurrió un error durante la siembra: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()