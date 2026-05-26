# ============================================================
# database/fix_admin.py — Corrige la contraseña del admin
# ============================================================
"""
Uso:  python database/fix_admin.py
Restablece la contraseña del administrador a: Admin@2024
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
import mysql.connector
from config import DB_CONFIG

DEFAULT_PASSWORD = "Admin@2024"

def _conn():
    skip = {"pool_name", "pool_size", "autocommit", "connection_timeout"}
    cfg  = {k: v for k, v in DB_CONFIG.items() if k not in skip}
    return mysql.connector.connect(**cfg)

def main():
    print(f"\n{'='*50}")
    print("  Corrección de contraseña — Admin")
    print(f"{'='*50}\n")

    # Generar hash correcto con bcrypt
    hashed = bcrypt.hashpw(
        DEFAULT_PASSWORD.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

    print(f"[·] Hash generado: {hashed[:30]}...")

    conn   = _conn()
    cursor = conn.cursor()

    # Actualizar el admin (identificación 1000000001)
    cursor.execute(
        "UPDATE employees SET password_hash=%s WHERE identification=%s",
        (hashed, "1000000001")
    )
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()

    if affected == 0:
        # El empleado no existe, insertarlo
        conn   = _conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO employees
               (identification, first_name, last_name, phone, email,
                role, password_hash, salary, active)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            ("1000000001", "Super", "Admin", "3001234567",
             "admin@dto2.com", "Administrador", hashed, 5000000.00, 1)
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("[✔] Admin creado desde cero.")
    else:
        print("[✔] Contraseña actualizada correctamente.")

    print(f"\n  → Usuario:    1000000001")
    print(f"  → Contraseña: {DEFAULT_PASSWORD}")
    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    main()
