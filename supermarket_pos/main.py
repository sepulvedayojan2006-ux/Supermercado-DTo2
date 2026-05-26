#!/usr/bin/env python3
# ============================================================
# main.py — Punto de entrada del Sistema POS DTo2
# ============================================================
"""
Ejecutar:
    python main.py

Requisitos previos:
    1. MySQL activo con las credenciales de config.py
    2. Base de datos inicializada:  python database/setup.py
    3. Dependencias instaladas:     pip install -r requirements.txt
"""

import sys
import os

# ── Asegurar que el directorio raíz esté en sys.path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ============================================================
# 1. Verificación de dependencias
# ============================================================
REQUIRED = {
    "mysql.connector": "mysql-connector-python",
    "bcrypt":          "bcrypt",
    "PIL":             "Pillow",
}
OPTIONAL = {
    "reportlab": "reportlab   (para generar facturas PDF)",
    "openpyxl":  "openpyxl    (para exportar reportes a Excel)",
}

missing_required = []
for module, pkg in REQUIRED.items():
    try:
        __import__(module)  
    except ImportError:
        missing_required.append(pkg)

if missing_required:
    print("\n╔══════════════════════════════════════════════════╗")
    print("║  ❌  Faltan dependencias obligatorias            ║")
    print("╚══════════════════════════════════════════════════╝")
    print("\nEjecuta el siguiente comando y vuelve a iniciar:\n")
    print(f"  pip install {' '.join(missing_required)}\n")
    sys.exit(1)

for module, pkg in OPTIONAL.items():
    try:
        __import__(module)
    except ImportError:
        print(f"[⚠] Opcional no instalado: {pkg}")


# ============================================================
# 2. Verificación de conexión MySQL
# ============================================================
def check_db_connection() -> bool:
    try:
        from database.connection import db
        return db.test_connection()
    except Exception as e:
        print(f"[✘] No se puede conectar a MySQL: {e}")
        return False


# ============================================================
# 3. Lanzar aplicación
# ============================================================
def main() -> None:
    print(f"\n{'='*50}")
    print("  Sistema POS — Supermercado DTo2  v1.0")
    print(f"{'='*50}")

    if not check_db_connection():
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error de Conexión",
            "No se pudo conectar a MySQL.\n\n"
            "Verifica:\n"
            "• Que el servidor MySQL esté activo\n"
            "• Las credenciales en config.py\n"
            "• Que hayas ejecutado: python database/setup.py"
        )
        root.destroy()
        sys.exit(1)

    print("[✔] Conexión a MySQL establecida.")
    print("[✔] Iniciando interfaz gráfica...\n")

    from ui.app import App
    app = App()
    app.run()


if __name__ == "__main__":
    main()
