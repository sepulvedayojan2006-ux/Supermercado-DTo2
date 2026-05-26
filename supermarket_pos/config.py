# ============================================================
# config.py — Configuración central del sistema
# ============================================================

import os

# --- Base del proyecto ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")

# --- Datos del negocio ---
COMPANY_NAME = "Supermercado DTo2"
COMPANY_NIT = "900.123.456-7"
COMPANY_ADDRESS = "Calle 10 # 5-20, Mocoa, Putumayo"
COMPANY_PHONE = "+57 312 345 6789"
COMPANY_EMAIL = "contacto@dto2.com"

# --- Base de datos MySQL ---
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "supermarket_dto2",
    "user": "root",
    "password": "",        # ← Cambia según tu entorno
    "charset": "utf8mb4",
    "autocommit": False,
    "connection_timeout": 10,
}

# --- Seguridad ---
BCRYPT_ROUNDS = 12
SESSION_TIMEOUT_MINUTES = 480        # 8 horas

# --- Inventario ---
LOW_STOCK_THRESHOLD = 10             # Alerta cuando stock < 10

# --- Facturación ---
INVOICE_PREFIX = "FAC"               # FAC-000001
TAX_RATE = 0.19                      # 19% IVA Colombia

# --- UI ---
THEME_PRIMARY   = "#1a6b36"          # Verde oscuro (logo)
THEME_SECONDARY = "#f5a623"          # Dorado (logo)
THEME_BG        = "#f4f6f9"
THEME_WHITE     = "#ffffff"
THEME_DANGER    = "#e74c3c"
THEME_SUCCESS   = "#27ae60"
THEME_WARNING   = "#f39c12"
THEME_TEXT      = "#2c3e50"
THEME_LIGHT     = "#ecf0f1"
FONT_FAMILY     = "Segoe UI"

# --- Roles ---
ROLE_ADMIN      = "Administrador"
ROLE_SUPERVISOR = "Supervisor"
ROLE_CASHIER    = "Cajero"
ALL_ROLES       = [ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_CASHIER]
