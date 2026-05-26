# 🛒 Sistema POS — Supermercado DTo2

Sistema de Punto de Venta completo desarrollado en **Python + Tkinter + MySQL**,
diseñado para la gestión integral de un supermercado.

---

## 📋 Tabla de Contenido
1. [Análisis y Elementos Faltantes](#1-análisis-y-elementos-faltantes)
2. [Requisitos Funcionales Mejorados](#2-requisitos-funcionales-mejorados)
3. [Requisitos No Funcionales](#3-requisitos-no-funcionales)
4. [Arquitectura Propuesta](#4-arquitectura-propuesta)
5. [Modelo de Clases](#5-modelo-de-clases)
6. [Modelo de Base de Datos](#6-modelo-de-base-de-datos)
7. [Estructura del Proyecto](#7-estructura-del-proyecto)
8. [Instalación y Ejecución](#8-instalación-y-ejecución)
9. [Roles y Permisos](#9-roles-y-permisos)
10. [Recomendaciones Futuras](#10-recomendaciones-futuras)

---

## 1. Análisis y Elementos Faltantes

El requerimiento original estaba bien planteado. Se identificaron y completaron estos elementos:

| Gap detectado | Solución implementada |
|---|---|
| Sin módulo de categorías | Tabla `categories`, combo en productos |
| Clientes no definidos | Entidad `Customer`, campo en ventas |
| Sin historial de movimientos | Tabla `inventory_movements` con auditoría completa |
| Sin manejo de IVA | Constante `TAX_RATE = 0.19`, cálculo automático |
| Factura sin IVA desglosado | PDF muestra subtotal, IVA y total por separado |
| Sin sesiones de auditoría | Tabla `sessions` para tracking de logins |
| Sin cancelación de ventas | `SaleService.cancel_sale()` restaura stock |
| Sin número consecutivo de compras | `PurchaseRepository.next_purchase_number()` |
| Sin alertas visuales de stock | Filas resaltadas en amarillo / rojo |
| Sin exportación de reportes | `ExcelExporter` + `InvoicePDFGenerator` |

---

## 2. Requisitos Funcionales Mejorados

### Módulo de Autenticación
- Login con identificación + contraseña hasheada (bcrypt, 12 rounds)
- Control de sesión activa (Singleton en `AuthService`)
- Bloqueo de cuenta al desactivar usuario

### Módulo de Empleados
- CRUD completo con validación de identificación única
- Cambio de contraseña independiente del resto de datos
- No se puede eliminar/desactivar la cuenta propia

### Módulo de Productos
- Búsqueda en tiempo real por nombre, código y código de barras
- Cálculo automático del margen de ganancia
- Alerta visual cuando `stock < min_stock`
- Vinculación con proveedor y categoría

### Módulo de Ventas
- Carrito interactivo con actualización de cantidades
- Verificación de stock en tiempo real al agregar
- Soporte para 3 métodos de pago
- Generación de factura PDF con logo corporativo
- Cancelación de venta con reversión automática de stock

### Módulo de Inventario
- Vista en tiempo real con tarjetas KPI
- Filtro de productos con bajo stock
- Ajuste manual con registro de movimiento
- Historial completo de movimientos por producto

### Módulo de Reportes
- 6 tipos de reportes con filtros por fecha
- Exportación a Excel con formato corporativo
- KPIs visuales en tarjetas de color

---

## 3. Requisitos No Funcionales

| Categoría | Especificación |
|---|---|
| **Seguridad** | Contraseñas bcrypt, control de acceso por rol en cada vista |
| **Rendimiento** | Pool de conexiones MySQL (5 conexiones) |
| **Usabilidad** | UI con tema corporativo, atajos de teclado, doble clic para editar |
| **Mantenibilidad** | Arquitectura en capas, principios SOLID, patrón Repository |
| **Portabilidad** | Compatible con Windows, macOS y Linux |
| **Escalabilidad** | Fácil adición de módulos por la arquitectura desacoplada |

---

## 4. Arquitectura Propuesta

Se usa **Arquitectura en Capas (Layered Architecture)** con **Patrón Repository**:

```
┌─────────────────────────────────────────┐
│          CAPA DE PRESENTACIÓN           │
│  ui/ → LoginView, DashboardView,        │
│         SalesView, ProductsView...      │
├─────────────────────────────────────────┤
│         CAPA DE LÓGICA DE NEGOCIO       │
│  services/ → AuthService, SaleService,  │
│              CartService, ReportService │
├─────────────────────────────────────────┤
│          CAPA DE ACCESO A DATOS         │
│  repositories/ → ProductRepository,    │
│                  SaleRepository...      │
├─────────────────────────────────────────┤
│              CAPA DE DATOS              │
│  MySQL — supermarket_dto2               │
│  database/connection.py (Singleton)     │
└─────────────────────────────────────────┘
```

### Patrones de diseño aplicados

| Patrón | Dónde | Descripción |
|---|---|---|
| **Singleton** | `DatabaseConnection` | Una única instancia del pool de conexiones |
| **Repository** | `ProductRepository`, etc. | Abstracción del acceso a datos |
| **Service Layer** | `SaleService`, `AuthService` | Orquesta la lógica de negocio |
| **Template Method** | `BaseEntity.validate()` | Contrato de validación en subclases |
| **Composite** | `Sale ←→ SaleDetail` | Composición de objetos |

### Principios SOLID aplicados

| Principio | Aplicación |
|---|---|
| **S** — Responsabilidad única | Cada clase hace una sola cosa |
| **O** — Abierto/Cerrado | Nuevos reportes sin modificar los existentes |
| **L** — Sustitución de Liskov | `BaseRepository` puede ser sustituido |
| **I** — Segregación de interfaces | `BaseRepository` con métodos mínimos |
| **D** — Inversión de dependencia | `Services` dependen de abstracciones, no implementaciones |

---

## 5. Modelo de Clases

```
BaseEntity (abstracta)
├── Employee          (identificación, rol, salario)
├── Category          (nombre, descripción)
├── Supplier          (NIT, contacto, dirección)
├── Product           (código, precios, stock)  ──── FK→ Category, Supplier
├── Sale              (factura, totales)         ──── FK→ Employee, Customer
│   └── SaleDetail[]  (producto, cantidad)       ──── FK→ Product
├── Purchase          (número, total)            ──── FK→ Supplier, Employee
│   └── PurchaseDetail[] (producto, costo)       ──── FK→ Product
├── Customer          (identificación, nombre)
└── InventoryMovement (tipo, cantidad, stock)    ──── FK→ Product, Employee

CartItem              (composición con Product, no persiste)
CartService           (agrega, quita, calcula totales)

BaseRepository (abstracta)
├── EmployeeRepository
├── ProductRepository
├── SaleRepository
├── SupplierRepository
├── CategoryRepository
├── PurchaseRepository
├── ReportRepository
└── InventoryMovementRepository

AuthService    → usa EmployeeRepository + bcrypt
EmployeeService → usa EmployeeRepository
ProductService  → usa ProductRepository + CategoryRepository
SaleService     → usa SaleRepository + ProductRepository + InventoryMovementRepository
CartService     → estado en memoria (no usa repositorio)
SupplierService → usa SupplierRepository
PurchaseService → usa PurchaseRepository + ProductRepository
ReportService   → usa ReportRepository
```

---

## 6. Modelo de Base de Datos

```sql
categories          (id, name, description, active)
employees           (id, identification, first_name, last_name, phone,
                     email, role, password_hash, salary, active)
sessions            (id, employee_id, login_at, logout_at)
suppliers           (id, name, nit, phone, email, address, contact_person, active)
products            (id, code, name, category_id FK, supplier_id FK,
                     purchase_price, sale_price, stock, min_stock, unit, barcode, active)
inventory_movements (id, product_id FK, employee_id FK, movement_type,
                     quantity, stock_before, stock_after, notes, reference_id)
customers           (id, identification, name, phone, email, address)
sales               (id, invoice_number UNIQUE, employee_id FK, customer_id FK,
                     subtotal, tax_amount, total, paid_amount, change_amount,
                     payment_method, status, sold_at)
sale_details        (id, sale_id FK, product_id FK, product_name,
                     unit_price, quantity, discount, subtotal)
purchases           (id, purchase_number UNIQUE, supplier_id FK, employee_id FK,
                     total, status, purchased_at)
purchase_details    (id, purchase_id FK, product_id FK, quantity, unit_cost, subtotal)
```

### Conexión a MySQL

En `config.py` configura:
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "supermarket_dto2",
    "user":     "root",
    "password": "TU_CONTRASEÑA",
}
```

El módulo `database/connection.py` implementa un **pool de 5 conexiones** usando
`mysql.connector.pooling.MySQLConnectionPool`. No es necesario gestionar conexiones
manualmente; el método `db.execute_query()` las obtiene y libera automáticamente.

---

## 7. Estructura del Proyecto

```
supermarket_pos/
├── main.py                    # Punto de entrada
├── config.py                  # Configuración global
├── requirements.txt
├── README.md
│
├── assets/
│   └── logo.jpg               # Logo corporativo DTo2
│
├── database/
│   ├── __init__.py
│   ├── connection.py          # Singleton pool MySQL
│   ├── schema.sql             # DDL completo + datos iniciales
│   └── setup.py               # Script de inicialización
│
├── models/
│   └── __init__.py            # Dataclasses: Employee, Product, Sale...
│
├── repositories/
│   └── __init__.py            # DAL: consultas SQL por entidad
│
├── services/
│   └── __init__.py            # Lógica de negocio + CartService
│
├── utils/
│   └── __init__.py            # Validators, PDF, Excel, Formatters
│
└── ui/
    ├── __init__.py
    ├── app.py                 # Ventana principal Tk
    ├── login_view.py          # Pantalla de login
    ├── dashboard_view.py      # Panel + pestañas por rol
    ├── sales_view.py          # Ventas y carrito
    ├── products_view.py       # CRUD productos
    ├── employees_view.py      # CRUD empleados
    ├── suppliers_view.py      # CRUD proveedores
    ├── inventory_view.py      # Stock + movimientos
    ├── reports_view.py        # Reportes + exportación
    └── components/
        └── __init__.py        # ThemeManager, DataTable, FormDialog...
```

---

## 8. Instalación y Ejecución

### Requisitos del sistema
- Python 3.10 o superior
- MySQL Server 8.0 o superior
- Sistema operativo: Windows 10/11, macOS 12+, Ubuntu 22+

### Paso 1 — Clonar / descomprimir el proyecto
```bash
cd supermarket_pos
```

### Paso 2 — Instalar dependencias
```bash
pip install -r requirements.txt
```
> En Linux con entorno controlado: `pip install -r requirements.txt --break-system-packages`

### Paso 3 — Configurar MySQL
Edita `config.py` con tus credenciales:
```python
DB_CONFIG = {
    "host":     "localhost",
    "password": "TU_CONTRASEÑA_MYSQL",
    ...
}
```

### Paso 4 — Inicializar la base de datos
```bash
python database/setup.py
```
Este script crea la BD, las tablas, las categorías y el usuario administrador.

### Paso 5 — Ejecutar la aplicación
```bash
python main.py
```

### Credenciales iniciales
| Campo | Valor |
|---|---|
| Identificación | `1000000001` |
| Contraseña     | `Admin@2024` |
| Rol            | Administrador |

---

## 9. Roles y Permisos

| Funcionalidad | Administrador | Supervisor | Cajero |
|---|:---:|:---:|:---:|
| Gestionar empleados | ✅ | ❌ | ❌ |
| Crear/eliminar productos | ✅ | ✅ | ❌ |
| Editar productos | ✅ | ✅ | ❌ |
| Gestionar proveedores | ✅ | ✅ | ❌ |
| Ajustar stock manualmente | ✅ | ✅ | ❌ |
| Procesar ventas | ✅ | ✅ | ✅ |
| Ver inventario | ✅ | ✅ | ✅ |
| Ver reportes | ✅ | ✅ | ✅ |
| Exportar reportes | ✅ | ✅ | ✅ |

---

## 10. Recomendaciones Futuras

| Mejora | Prioridad | Descripción |
|---|---|---|
| **Lector de código de barras** | Alta | Integrar con `pynput` para escanear físicamente |
| **Módulo de turnos** | Alta | Control de apertura/cierre de caja con arqueo |
| **Facturación electrónica DIAN** | Alta | API DIAN para Colombia (para operación real) |
| **Dashboard gráfico** | Media | Gráficas con `matplotlib` o `plotly` |
| **API REST** | Media | Flask/FastAPI para acceso desde móviles |
| **Respaldo automático de BD** | Media | Script de dump diario con `mysqldump` |
| **Módulo de devoluciones** | Media | Flujo formal de devolución con nota crédito |
| **Fidelización de clientes** | Baja | Puntos, historial de compras por cliente |
| **Multi-sucursal** | Baja | Tabla `branches`, sincronización entre sedes |
| **App móvil** | Baja | Android/iOS para consulta de inventario |
