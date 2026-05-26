-- ============================================================
-- schema.sql — Esquema completo de base de datos MySQL
-- Sistema POS Supermercado DTo2
-- ============================================================

CREATE DATABASE IF NOT EXISTS supermarket_dto2
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE supermarket_dto2;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- 1. CATEGORÍAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(80)  NOT NULL UNIQUE,
    description VARCHAR(255),
    active      TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 2. USUARIOS / EMPLEADOS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    identification  VARCHAR(20)  NOT NULL UNIQUE,
    first_name      VARCHAR(80)  NOT NULL,
    last_name       VARCHAR(80)  NOT NULL,
    phone           VARCHAR(20),
    email           VARCHAR(120) UNIQUE,
    role            ENUM('Administrador','Supervisor','Cajero') NOT NULL DEFAULT 'Cajero',
    password_hash   VARCHAR(255) NOT NULL,
    salary          DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    active          TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 3. SESIONES (auditoría de logins)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_id INT UNSIGNED NOT NULL,
    login_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logout_at   DATETIME,
    ip_address  VARCHAR(45),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 4. PROVEEDORES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    nit             VARCHAR(30)  NOT NULL UNIQUE,
    phone           VARCHAR(20),
    email           VARCHAR(120),
    address         VARCHAR(255),
    contact_person  VARCHAR(120),
    active          TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 5. PRODUCTOS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code            VARCHAR(30)  NOT NULL UNIQUE,
    name            VARCHAR(150) NOT NULL,
    description     TEXT,
    category_id     INT UNSIGNED NOT NULL,
    supplier_id     INT UNSIGNED,
    purchase_price  DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    sale_price      DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    stock           INT          NOT NULL DEFAULT 0,
    min_stock       INT          NOT NULL DEFAULT 10,
    unit            VARCHAR(20)  NOT NULL DEFAULT 'unidad',
    barcode         VARCHAR(50),
    active          TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 6. MOVIMIENTOS DE INVENTARIO
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_movements (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_id      INT UNSIGNED NOT NULL,
    employee_id     INT UNSIGNED NOT NULL,
    movement_type   ENUM('compra','venta','devolucion','ajuste') NOT NULL,
    quantity        INT          NOT NULL,
    stock_before    INT          NOT NULL,
    stock_after     INT          NOT NULL,
    notes           VARCHAR(255),
    reference_id    INT UNSIGNED,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id)  REFERENCES products(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 7. CLIENTES (opcional, para facturación nominada)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    identification  VARCHAR(30)  NOT NULL UNIQUE,
    name            VARCHAR(150) NOT NULL,
    phone           VARCHAR(20),
    email           VARCHAR(120),
    address         VARCHAR(255),
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 8. VENTAS (cabecera)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    invoice_number  VARCHAR(20)  NOT NULL UNIQUE,
    employee_id     INT UNSIGNED NOT NULL,
    customer_id     INT UNSIGNED,
    subtotal        DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    tax_amount      DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total           DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    paid_amount     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    change_amount   DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    payment_method  ENUM('efectivo','tarjeta','transferencia') NOT NULL DEFAULT 'efectivo',
    status          ENUM('completada','anulada','devuelta') NOT NULL DEFAULT 'completada',
    notes           VARCHAR(255),
    sold_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 9. DETALLE DE VENTAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sale_details (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sale_id         INT UNSIGNED  NOT NULL,
    product_id      INT UNSIGNED  NOT NULL,
    product_name    VARCHAR(150)  NOT NULL,
    unit_price      DECIMAL(12,2) NOT NULL,
    quantity        INT           NOT NULL,
    discount        DECIMAL(5,2)  NOT NULL DEFAULT 0.00,
    subtotal        DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (sale_id)    REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 10. COMPRAS A PROVEEDORES (cabecera)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchases (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_number VARCHAR(20)   NOT NULL UNIQUE,
    supplier_id     INT UNSIGNED  NOT NULL,
    employee_id     INT UNSIGNED  NOT NULL,
    total           DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    status          ENUM('recibida','pendiente','cancelada') NOT NULL DEFAULT 'recibida',
    notes           VARCHAR(255),
    purchased_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 11. DETALLE DE COMPRAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_details (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_id     INT UNSIGNED  NOT NULL,
    product_id      INT UNSIGNED  NOT NULL,
    quantity        INT           NOT NULL,
    unit_cost       DECIMAL(12,2) NOT NULL,
    subtotal        DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)  REFERENCES products(id)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- DATOS INICIALES
-- ============================================================

-- Categorías base
INSERT IGNORE INTO categories (name, description) VALUES
('Lácteos',        'Leche, queso, yogur, mantequilla'),
('Carnes',         'Res, cerdo, pollo, embutidos'),
('Frutas y Verduras', 'Productos frescos de temporada'),
('Panadería',      'Pan, galletas, tortas, pasteles'),
('Bebidas',        'Agua, jugos, gaseosas, cervezas'),
('Limpieza',       'Detergentes, desinfectantes, escobas'),
('Aseo Personal',  'Champú, jabón, desodorante, pañales'),
('Granos y Cereales','Arroz, lentejas, maíz, avena'),
('Congelados',     'Helados, comidas listas, papas fritas'),
('Snacks',         'Papas fritas, chocolates, caramelos');

-- Administrador por defecto  (contraseña: Admin@2024)
-- Hash bcrypt generado con rounds=12
INSERT IGNORE INTO employees
    (identification, first_name, last_name, phone, email, role, password_hash, salary)
VALUES
    ('1000000001', 'Super', 'Admin', '3001234567', 'admin@dto2.com',
     'Administrador',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMqJqhCanUXtiT2QCG2aXQT7yO',
     5000000.00);
-- NOTA: Al iniciar la app por primera vez usa: ID=1000000001 / Pass=Admin@2024

-- Proveedor de ejemplo
INSERT IGNORE INTO suppliers (name, nit, phone, email, address, contact_person) VALUES
('Distribuidora La Cosecha', '860.012.345-1', '6012345678',
 'ventas@lacosecha.com', 'Cra 7 # 12-34, Bogotá', 'Carlos Rodríguez'),
('Lácteos del Sur Ltda.',    '830.456.789-2', '6023456789',
 'info@lacteossur.com',  'Av 30 # 5-10, Pasto', 'María López');
