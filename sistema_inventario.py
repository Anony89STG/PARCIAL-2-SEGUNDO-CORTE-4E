import os
import sqlite3
from datetime import datetime

# Definir la ruta de la base de datos en el mismo directorio del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "Inventario_electronica.db")

# ==============================================================================
# CONEXIÓN Y CONFIGURACIÓN DE BASE DE DATOS
# ==============================================================================

def iniciar_conexion():
    """Creación de conexión a SQLite habilitando las claves foráneas."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_bd():
    """Crear la tabla de productos y ventas si no existen."""
    try:
        with iniciar_conexion() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    precio REAL NOT NULL CHECK(precio > 0),
                    cantidad INTEGER NOT NULL CHECK(cantidad >= 0)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    cantidad_vendida INTEGER NOT NULL CHECK(cantidad_vendida > 0),
                    total REAL NOT NULL CHECK(total > 0),
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                );
            """)
            conn.commit()
            print("Tablas verificadas/creadas exitosamente.")
    
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")


# ==============================================================================
# OPERACIONES DE CRUD DE PRODUCTOS (PARTE 2)
# ==============================================================================

def registrar_productos():
    """1. Registra un nuevo producto en la base de datos."""
    print("\n--- REGISTRAR NUEVO PRODUCTO ---")
    nombre = input("Nombre del componente electrónico: ").strip()
    if not nombre:
        print("[!] Error: El nombre del producto no puede estar vacío.")
        return

    try:
        precio = float(input("Precio unitario ($): "))
        cantidad = int(input("Cantidad inicial en inventario: "))
        if precio <= 0 or cantidad < 0:
            print("[!] Error: El precio debe ser mayor a 0 y la cantidad no puede ser negativa.")
            return
    except ValueError:
        print("[!] Error: Debes ingresar valores numéricos válidos para precio y cantidad.")
        return

    conn = iniciar_conexion()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO productos (nombre, precio, cantidad) VALUES (?, ?, ?)",
            (nombre, precio, cantidad)
        )
        conn.commit()
        print(f"[OK] Producto '{nombre}' registrado con éxito (ID asignado: {cursor.lastrowid}).")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[ERROR] No se pudo registrar el producto: {e}")
    finally:
        conn.close()


def consultar_productos():
    """2. Consulta y muestra todos los productos registrados."""
    print("\n--- INVENTARIO DE PRODUCTOS ---")
    conn = iniciar_conexion()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, precio, cantidad FROM productos ORDER BY id ASC")
        productos = cursor.fetchall()

        if not productos:
            print("No hay productos registrados en el inventario.")
            return False

        print(f"{'ID':<5} | {'COMPONENTE ELECTRÓNICO':<32} | {'PRECIO ($)':>12} | {'STOCK':>8}")
        print("-" * 66)
        for prod_id, nombre, precio, cantidad in productos:
            print(f"{prod_id:<5} | {nombre:<32} | ${precio:>11,.2f} | {cantidad:>8}")
        print("-" * 66)
        return True
    except sqlite3.Error as e:
        print(f"[ERROR] Al consultar los productos: {e}")
        return False
    finally:
        conn.close()


def actualizar_productos():
    """3. Actualiza el precio, la cantidad o ambos de un producto existente."""
    print("\n--- ACTUALIZAR PRODUCTO ---")
    if not consultar_productos():
        return

    try:
        producto_id = int(input("Ingrese el ID del producto que desea actualizar: "))
    except ValueError:
        print("[!] Error: El ID debe ser un número entero.")
        return

    conn = iniciar_conexion()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, precio, cantidad FROM productos WHERE id = ?", (producto_id,))
        producto = cursor.fetchone()

        if not producto:
            print(f"[!] Error: No se encontró ningún producto con ID {producto_id}.")
            return

        _, nombre, precio_actual, cantidad_actual = producto
        print(f"\nProducto seleccionado: {nombre}")
        print(f"Valores actuales -> Precio: ${precio_actual:,.2f} | Stock: {cantidad_actual}")
        print("¿Qué desea modificar?")
        print("1. Solo Precio")
        print("2. Solo Cantidad (Stock)")
        print("3. Ambos (Precio y Cantidad)")
        print("0. Cancelar")

        opcion = input("Seleccione una opción (0-3): ").strip()

        nuevo_precio = precio_actual
        nueva_cantidad = cantidad_actual

        if opcion == "1":
            nuevo_precio = float(input("Ingrese el nuevo precio ($): "))
            if nuevo_precio <= 0:
                print("[!] Error: El precio debe ser mayor a 0.")
                return
        elif opcion == "2":
            nueva_cantidad = int(input("Ingrese la nueva cantidad en inventario: "))
            if nueva_cantidad < 0:
                print("[!] Error: La cantidad no puede ser negativa.")
                return
        elif opcion == "3":
            nuevo_precio = float(input("Ingrese el nuevo precio ($): "))
            nueva_cantidad = int(input("Ingrese la nueva cantidad en inventario: "))
            if nuevo_precio <= 0 or nueva_cantidad < 0:
                print("[!] Error: El precio debe ser mayor a 0 y la cantidad no puede ser negativa.")
                return
        elif opcion == "0":
            print("Operación cancelada.")
            return
        else:
            print("[!] Opción inválida.")
            return

        cursor.execute(
            "UPDATE productos SET precio = ?, cantidad = ? WHERE id = ?",
            (nuevo_precio, nueva_cantidad, producto_id)
        )
        conn.commit()
        print(f"[OK] Producto '{nombre}' actualizado con éxito. Nuevo precio: ${nuevo_precio:,.2f} | Nuevo stock: {nueva_cantidad}")

    except ValueError:
        print("[!] Error: Ingrese valores numéricos válidos.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[ERROR] No se pudo actualizar el producto: {e}")
    finally:
        conn.close()


def eliminar_productos():
    """4. Elimina un producto de la base de datos respetando la integridad referencial."""
    print("\n--- ELIMINAR PRODUCTO ---")
    if not consultar_productos():
        return

    try:
        producto_id = int(input("Ingrese el ID del producto que desea eliminar: "))
    except ValueError:
        print("[!] Error: El ID debe ser un número entero.")
        return

    conn = iniciar_conexion()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM productos WHERE id = ?", (producto_id,))
        producto = cursor.fetchone()

        if not producto:
            print(f"[!] Error: No se encontró ningún producto con ID {producto_id}.")
            return

        _, nombre = producto
        confirmacion = input(f"¿Está seguro de que desea eliminar el producto '{nombre}' (ID: {producto_id})? (s/n): ").strip().lower()
        if confirmacion != "s":
            print("Operación cancelada. El producto no fue eliminado.")
            return

        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conn.commit()
        print(f"[OK] El producto '{nombre}' (ID: {producto_id}) fue eliminado exitosamente.")

    except sqlite3.IntegrityError:
        # Se activa por PRAGMA foreign_keys = ON cuando el producto tiene ventas en la tabla 'ventas'
        conn.rollback()
        print("\n[!] ERROR DE INTEGRIDAD REFERENCIAL:")
        print(f"No se puede eliminar el producto '{nombre}' (ID: {producto_id}) porque tiene ventas registradas en el historial.")
        print("La base de datos protege los registros para no generar inconsistencias.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[ERROR] No se pudo eliminar el producto: {e}")
    finally:
        conn.close()


# ==============================================================================
# GESTIÓN DE VENTAS Y TRANSACCIONES (PARTE 3)
# ==============================================================================

def procesar_ventas(producto_id, cantidad_vendida, simular_error=False):
    """
    Ejecución de la lógica transaccional de las ventas:
    1. Verifica que el producto exista.
    2. Comprueba que haya suficientes unidades.
    3. Registra la venta en la tabla 'ventas'.
    4. (Si simular_error=True, provoca un fallo antes de descontar inventario).
    5. Descuenta las unidades vendidas del inventario en 'productos'.
    6. Confirma con commit() o revierte todo con rollback() en caso de fallo.
    """
    if cantidad_vendida <= 0:
        print("[!] Error en la validación: la cantidad a vender debe ser mayor a 0.")
        return

    conn = iniciar_conexion()
    try:
        cursor = conn.cursor()

        # Paso 1: Verificación de producto
        cursor.execute("SELECT id, nombre, precio, cantidad FROM productos WHERE id = ?", (producto_id,))
        producto = cursor.fetchone()

        if not producto:
            print(f"[!] Error: No existe el producto con ID {producto_id}.")
            return

        prod_id, nombre, precio_unitario, stock_actual = producto

        # Paso 2: Comprobar si hay unidades disponibles
        if stock_actual < cantidad_vendida:
            print(f"[!] Advertencia: Stock insuficiente para '{nombre}'. Disponibles: {stock_actual}")
            print(f"Unidades solicitadas: {cantidad_vendida}")
            return

        total_venta = round(precio_unitario * cantidad_vendida, 2)
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n[TRANSACCIÓN] Iniciando registro de venta para '{nombre}'...")

        # Paso 3: Registrar la venta en la base de datos (Inicia transacción en SQLite)
        cursor.execute(
            "INSERT INTO ventas (producto_id, cantidad_vendida, total, fecha) VALUES (?, ?, ?, ?)",
            (prod_id, cantidad_vendida, total_venta, fecha_actual)
        )
        print("  -> Paso 1/2 completado: Venta insertada en tabla 'ventas'.")

        # RETO OBLIGATORIO: Provocar un error controlado después de registrar la venta
        # pero antes de actualizar el inventario.
        if simular_error:
            print("  -> [!] Provocando error controlado antes de descontar el inventario...")
            raise RuntimeError(
                "Fallo simulado de conexión/sistema después de INSERT en 'ventas' y antes de UPDATE en 'productos'."
            )

        # Paso 4: Descontar las unidades vendidas del inventario
        cursor.execute(
            "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
            (cantidad_vendida, prod_id)
        )
        print("  -> Paso 2/2 completado: Inventario descontado en tabla 'productos'.")

        # Paso 5: Confirmar ambas operaciones mediante commit()
        conn.commit()
        print(
            f"[OK - COMMIT EXITOSO] Venta registrada correctamente.\n"
            f"     Producto: {nombre} | Cantidad: {cantidad_vendida} | Total: ${total_venta:,.2f} | "
            f"Nuevo stock: {stock_actual - cantidad_vendida}"
        )

    except Exception as e:
        # Si ocurre cualquier error, se cancela toda la operación con rollback()
        conn.rollback()
        print(f"\n[ALERTA - EXCEPCIÓN DETECTADA]: {e}")
        print(
            "[ROLLBACK EJECUTADO] Se canceló toda la transacción.\n"
            "La venta NO fue guardada y el stock del producto permanece intacto."
        )
    finally:
        conn.close()


def registrar_venta_menu():
    """Solicita los datos al usuario para realizar una venta (con opción de simular error para probar rollback)."""
    if not consultar_productos():
        return

    print("\n--- REGISTRAR NUEVA VENTA ---")

    try:
        producto_id = int(input("Ingrese el ID del producto a vender: "))
        cantidad_vendida = int(input("Ingrese la cantidad de unidades a vender: "))
        if producto_id <= 0 or cantidad_vendida <= 0:
            print("[!] Error: El ID y la cantidad deben ser enteros positivos mayores a 0.")
            return
    except ValueError:
        print("[!] Error: Debe ingresar números enteros para el ID y la cantidad.")
        return

    # Opción para provocar el error controlado y demostrar el rollback
    resp = input("¿Desea forzar un error en el sistema antes de descontar stock para probar el rollback? (s/n) [n]: ").strip().lower()
    simular_error = resp in ("s", "si", "sí", "y", "yes")

    if simular_error:
        print("\n=== GENERANDO ERROR CONTROLADO Y DEMOSTRANDO ROLLBACK ===")

    procesar_ventas(producto_id, cantidad_vendida, simular_error=simular_error)

    if simular_error:
        print("\n--- VERIFICACIÓN AUTOMÁTICA DE INTEGRIDAD TRAS EL ROLLBACK ---")
        consultar_productos()
        mostrar_historial_ventas()


def mostrar_historial_ventas():
    """6. Muestra el historial de ventas incluyendo el nombre del producto mediante JOIN."""
    print("\n--- HISTORIAL DE VENTAS ---")
    conn = iniciar_conexion()
    try:
        cursor = conn.cursor()
        consulta_join = """
            SELECT 
                v.id,
                p.nombre AS nombre_producto,
                v.cantidad_vendida,
                v.total,
                v.fecha
            FROM ventas v
            INNER JOIN productos p ON v.producto_id = p.id
            ORDER BY v.id DESC;
        """
        cursor.execute(consulta_join)
        ventas = cursor.fetchall()

        if not ventas:
            print("Aún no existen ventas registradas.")
            return

        print(f"{'ID VENTA':<9} | {'COMPONENTE ELECTRÓNICO':<28} | {'CANT.':>6} | {'TOTAL ($)':>12} | {'FECHA Y HORA':<19}")
        print("-" * 86)
        for v_id, nombre_prod, cant, total, fecha in ventas:
            print(f"{v_id:<9} | {nombre_prod:<28} | {cant:>6} | ${total:>11,.2f} | {fecha:<19}")
        print("-" * 86)
    except sqlite3.Error as e:
        print(f"[ERROR] Al consultar el historial de ventas: {e}")
    finally:
        conn.close()


# ==============================================================================
# MENÚ INTERACTIVO PRINCIPAL
# ==============================================================================

def menu_principal():
    inicializar_bd()

    while True:
        print("\n" + "=" * 66)
        print("   SISTEMA DE INVENTARIO Y VENTAS - COMPONENTES ELECTRÓNICOS")
        print("=" * 66)
        print("1. Registrar producto")
        print("2. Consultar todos los productos")
        print("3. Actualizar producto")
        print("4. Eliminar producto")
        print("5. Registrar una venta")
        print("6. Mostrar historial de ventas")
        print("0. Salir")
        print("=" * 66)

        opcion = input("Seleccione una opción (0-6): ").strip()

        if opcion == "1":
            registrar_productos()
        elif opcion == "2":
            consultar_productos()
        elif opcion == "3":
            actualizar_productos()
        elif opcion == "4":
            eliminar_productos()
        elif opcion == "5":
            registrar_venta_menu()
        elif opcion == "6":
            mostrar_historial_ventas()
        elif opcion == "0":
            print("Cerrando el sistema de inventario y ventas. ¡Hasta luego!")
            break
        else:
            print("[!] Opción no válida. Por favor seleccione un número entre 0 y 6.")


if __name__ == "__main__":
    menu_principal()
