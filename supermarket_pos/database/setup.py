# ============================================================
# database/setup.py — Inicialización de la base de datos
# ============================================================
"""
Ejecuta este script UNA SOLA VEZ para crear la BD y las tablas.
Uso:  python database/setup.py
"""

import os
import sys
import re

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG, COMPANY_NAME


# ──────────────────────────────────────────────────────────
def _base_cfg() -> dict:
    """Config sin 'database', 'pool_name', 'pool_size', 'autocommit'."""
    skip = {"database", "pool_name", "pool_size", "autocommit",
            "connection_timeout"}
    return {k: v for k, v in DB_CONFIG.items() if k not in skip}


def _conn_no_db() -> mysql.connector.MySQLConnection:
    """Conexión sin base de datos seleccionada (para crearla)."""
    return mysql.connector.connect(**_base_cfg())


def _conn_with_db() -> mysql.connector.MySQLConnection:
    """Conexión ya apuntando a la base de datos del proyecto."""
    cfg = {**_base_cfg(), "database": DB_CONFIG["database"]}
    return mysql.connector.connect(**cfg)


# ──────────────────────────────────────────────────────────
def create_database() -> bool:
    print(f"\n{'='*56}")
    print(f"  Configuración de BD — {COMPANY_NAME}")
    print(f"{'='*56}")
    try:
        conn   = _conn_no_db()
        cursor = conn.cursor()
        db     = DB_CONFIG["database"]
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        print(f"[✔] Base de datos '{db}' verificada / creada.")
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"[✘] Error al crear la base de datos: {e}")
        print("\n  Verifica en config.py:")
        print(f"    host     = {DB_CONFIG.get('host')}")
        print(f"    port     = {DB_CONFIG.get('port')}")
        print(f"    user     = {DB_CONFIG.get('user')}")
        print(f"    password = {'*' * len(str(DB_CONFIG.get('password', '')))}")
        return False


# ──────────────────────────────────────────────────────────
def _clean_sql(raw: str) -> list[str]:
    """
    Prepara la lista de sentencias SQL limpias desde el archivo.
    Elimina comentarios de línea (--) y de bloque (/* */),
    luego divide por ';' ignorando vacíos.
    """
    # Quitar comentarios de bloque /* ... */
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    # Quitar comentarios de línea -- ...
    raw = re.sub(r"--[^\n]*", "", raw)
    # Dividir por ';' y limpiar
    stmts = []
    for s in raw.split(";"):
        s = s.strip()
        if s:
            stmts.append(s)
    return stmts


def run_schema() -> bool:
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_path):
        print("[✘] No se encontró schema.sql")
        return False
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            raw_sql = f.read()

        statements = _clean_sql(raw_sql)
        print(f"[·] {len(statements)} sentencias SQL encontradas en schema.sql")

        # Conectar CON la base de datos ya seleccionada
        conn   = _conn_with_db()
        cursor = conn.cursor()

        executed = 0
        skipped  = 0
        for stmt in statements:
            upper = stmt.upper().lstrip()
            # Saltar USE y sentencias vacías
            if upper.startswith("USE ") or upper.startswith("CREATE DATABASE"):
                skipped += 1
                continue
            try:
                cursor.execute(stmt)
                # Consumir resultados si los hay (p.ej. SELECT en INSERT...SELECT)
                if cursor.with_rows:
                    cursor.fetchall()
                executed += 1
            except Error as e:
                # 1050 = Table already exists
                # 1062 = Duplicate entry (INSERT IGNORE no siempre previene esto)
                # 1007 = Database already exists
                if e.errno in (1050, 1062, 1007):
                    skipped += 1
                else:
                    print(f"  [!] Advertencia (sentencia ignorada): {e}")
                    skipped += 1

        conn.commit()
        print(f"[✔] Esquema aplicado — ejecutadas: {executed}, omitidas: {skipped}")
        cursor.close()
        conn.close()
        return True

    except Error as e:
        print(f"[✘] Error al ejecutar el esquema: {e}")
        return False


# ──────────────────────────────────────────────────────────
def verify_setup() -> None:
    try:
        conn   = _conn_with_db()
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"[✔] Tablas creadas: {', '.join(tables)}")

        cursor.execute("SELECT COUNT(*) FROM employees")
        emp_count = cursor.fetchone()[0]
        print(f"[✔] Empleados registrados : {emp_count}")

        cursor.execute("SELECT COUNT(*) FROM categories")
        cat_count = cursor.fetchone()[0]
        print(f"[✔] Categorías registradas: {cat_count}")

        cursor.execute("SELECT COUNT(*) FROM suppliers")
        sup_count = cursor.fetchone()[0]
        print(f"[✔] Proveedores registrados: {sup_count}")

        cursor.close()
        conn.close()
    except Error as e:
        print(f"[!] Error en verificación final: {e}")


# ──────────────────────────────────────────────────────────
def main() -> None:
    print("\nIniciando configuración del sistema...\n")

    if not create_database():
        sys.exit(1)

    if not run_schema():
        sys.exit(1)

    verify_setup()

    print("\n" + "="*56)
    print("  ✅  Base de datos lista para usar.")
    print("  → Ejecuta ahora:  python main.py")
    print("  → Usuario admin:  1000000001")
    print("  → Contraseña:     Admin@2024")
    print("="*56 + "\n")


if __name__ == "__main__":
    main()
