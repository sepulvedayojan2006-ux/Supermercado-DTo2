# ============================================================
# repositories/__init__.py — Capa de Acceso a Datos (DAL)
# ============================================================
"""
Patrón Repository: abstrae el acceso a la BD.
Principio de Responsabilidad Única (SRP) de SOLID.
Cada repositorio gestiona UNA entidad.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional
from database.connection import db
from models import (
    Category, Employee, Supplier, Product,
    Sale, SaleDetail, Purchase, PurchaseDetail,
    Customer, InventoryMovement
)


# ============================================================
# BASE REPOSITORY — Abstracción + Polimorfismo
# ============================================================
class BaseRepository(ABC):
    """Interfaz genérica para todos los repositorios."""

    @abstractmethod
    def find_by_id(self, entity_id: int):
        pass

    @abstractmethod
    def find_all(self) -> list:
        pass

    @abstractmethod
    def save(self, entity) -> int:
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        pass


# ============================================================
# CATEGORY REPOSITORY
# ============================================================
class CategoryRepository(BaseRepository):

    def find_by_id(self, entity_id: int) -> Optional[Category]:
        row = db.execute_query(
            "SELECT * FROM categories WHERE id=%s", (entity_id,), fetch_one=True
        )
        return self._map(row) if row else None

    def find_all(self) -> list[Category]:
        rows = db.execute_query("SELECT * FROM categories ORDER BY name", fetch=True)
        return [self._map(r) for r in rows]

    def find_active(self) -> list[Category]:
        rows = db.execute_query(
            "SELECT * FROM categories WHERE active=1 ORDER BY name", fetch=True
        )
        return [self._map(r) for r in rows]

    def save(self, cat: Category) -> int:
        if cat.id:
            db.execute_query(
                "UPDATE categories SET name=%s, description=%s, active=%s WHERE id=%s",
                (cat.name, cat.description, int(cat.active), cat.id), commit=True
            )
            return cat.id
        return db.execute_query(
            "INSERT INTO categories (name, description) VALUES (%s,%s)",
            (cat.name, cat.description), commit=True
        )

    def delete(self, entity_id: int) -> bool:
        db.execute_query(
            "UPDATE categories SET active=0 WHERE id=%s", (entity_id,), commit=True
        )
        return True

    @staticmethod
    def _map(row: dict) -> Category:
        from datetime import datetime
        return Category(
            id=row["id"], name=row["name"], description=row.get("description",""),
            active=bool(row["active"]),
            created_at=row.get("created_at"), updated_at=row.get("updated_at")
        )


# ============================================================
# EMPLOYEE REPOSITORY
# ============================================================
class EmployeeRepository(BaseRepository):

    def find_by_id(self, entity_id: int) -> Optional[Employee]:
        row = db.execute_query(
            "SELECT * FROM employees WHERE id=%s", (entity_id,), fetch_one=True
        )
        return self._map(row) if row else None

    def find_by_identification(self, identification: str) -> Optional[Employee]:
        row = db.execute_query(
            "SELECT * FROM employees WHERE identification=%s", (identification,), fetch_one=True
        )
        return self._map(row) if row else None

    def find_all(self) -> list[Employee]:
        rows = db.execute_query(
            "SELECT * FROM employees ORDER BY last_name, first_name", fetch=True
        )
        return [self._map(r) for r in rows]

    def find_active(self) -> list[Employee]:
        rows = db.execute_query(
            "SELECT * FROM employees WHERE active=1 ORDER BY last_name", fetch=True
        )
        return [self._map(r) for r in rows]

    def save(self, emp: Employee) -> int:
        if emp.id:
            db.execute_query(
                """UPDATE employees SET identification=%s, first_name=%s, last_name=%s,
                   phone=%s, email=%s, role=%s, salary=%s, active=%s WHERE id=%s""",
                (emp.identification, emp.first_name, emp.last_name,
                 emp.phone, emp.email, emp.role, emp.salary, int(emp.active), emp.id),
                commit=True
            )
            return emp.id
        return db.execute_query(
            """INSERT INTO employees
               (identification,first_name,last_name,phone,email,role,password_hash,salary)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (emp.identification, emp.first_name, emp.last_name, emp.phone,
             emp.email, emp.role, emp.password_hash, emp.salary),
            commit=True
        )

    def update_password(self, emp_id: int, password_hash: str) -> None:
        db.execute_query(
            "UPDATE employees SET password_hash=%s WHERE id=%s",
            (password_hash, emp_id), commit=True
        )

    def delete(self, entity_id: int) -> bool:
        db.execute_query(
            "UPDATE employees SET active=0 WHERE id=%s", (entity_id,), commit=True
        )
        return True

    @staticmethod
    def _map(row: dict) -> Employee:
        return Employee(
            id=row["id"], identification=row["identification"],
            first_name=row["first_name"], last_name=row["last_name"],
            phone=row.get("phone",""), email=row.get("email",""),
            role=row["role"], password_hash=row["password_hash"],
            salary=float(row["salary"]), active=bool(row["active"]),
            created_at=row.get("created_at"), updated_at=row.get("updated_at")
        )


# ============================================================
# SUPPLIER REPOSITORY
# ============================================================
class SupplierRepository(BaseRepository):

    def find_by_id(self, entity_id: int) -> Optional[Supplier]:
        row = db.execute_query(
            "SELECT * FROM suppliers WHERE id=%s", (entity_id,), fetch_one=True
        )
        return self._map(row) if row else None

    def find_all(self) -> list[Supplier]:
        rows = db.execute_query("SELECT * FROM suppliers ORDER BY name", fetch=True)
        return [self._map(r) for r in rows]

    def find_active(self) -> list[Supplier]:
        rows = db.execute_query(
            "SELECT * FROM suppliers WHERE active=1 ORDER BY name", fetch=True
        )
        return [self._map(r) for r in rows]

    def save(self, sup: Supplier) -> int:
        if sup.id:
            db.execute_query(
                """UPDATE suppliers SET name=%s,nit=%s,phone=%s,email=%s,
                   address=%s,contact_person=%s,active=%s WHERE id=%s""",
                (sup.name, sup.nit, sup.phone, sup.email,
                 sup.address, sup.contact_person, int(sup.active), sup.id),
                commit=True
            )
            return sup.id
        return db.execute_query(
            """INSERT INTO suppliers (name,nit,phone,email,address,contact_person)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (sup.name, sup.nit, sup.phone, sup.email, sup.address, sup.contact_person),
            commit=True
        )

    def delete(self, entity_id: int) -> bool:
        db.execute_query(
            "UPDATE suppliers SET active=0 WHERE id=%s", (entity_id,), commit=True
        )
        return True

    @staticmethod
    def _map(row: dict) -> Supplier:
        return Supplier(
            id=row["id"], name=row["name"], nit=row["nit"],
            phone=row.get("phone",""), email=row.get("email",""),
            address=row.get("address",""), contact_person=row.get("contact_person",""),
            active=bool(row["active"]),
            created_at=row.get("created_at"), updated_at=row.get("updated_at")
        )


# ============================================================
# PRODUCT REPOSITORY
# ============================================================
class ProductRepository(BaseRepository):

    _BASE = """
        SELECT p.*, c.name AS category_name, s.name AS supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers  s ON p.supplier_id  = s.id
    """

    def find_by_id(self, entity_id: int) -> Optional[Product]:
        row = db.execute_query(
            self._BASE + " WHERE p.id=%s", (entity_id,), fetch_one=True
        )
        return self._map(row) if row else None

    def find_by_code(self, code: str) -> Optional[Product]:
        row = db.execute_query(
            self._BASE + " WHERE p.code=%s", (code,), fetch_one=True
        )
        return self._map(row) if row else None

    def find_all(self) -> list[Product]:
        rows = db.execute_query(self._BASE + " ORDER BY p.name", fetch=True)
        return [self._map(r) for r in rows]

    def find_active(self) -> list[Product]:
        rows = db.execute_query(
            self._BASE + " WHERE p.active=1 ORDER BY p.name", fetch=True
        )
        return [self._map(r) for r in rows]

    def search(self, term: str) -> list[Product]:
        like = f"%{term}%"
        rows = db.execute_query(
            self._BASE + " WHERE p.active=1 AND (p.name LIKE %s OR p.code LIKE %s OR p.barcode LIKE %s)",
            (like, like, like), fetch=True
        )
        return [self._map(r) for r in rows]

    def find_low_stock(self) -> list[Product]:
        rows = db.execute_query(
            self._BASE + " WHERE p.active=1 AND p.stock < p.min_stock ORDER BY p.stock",
            fetch=True
        )
        return [self._map(r) for r in rows]

    def save(self, prod: Product) -> int:
        if prod.id:
            db.execute_query(
                """UPDATE products SET code=%s,name=%s,description=%s,category_id=%s,
                   supplier_id=%s,purchase_price=%s,sale_price=%s,stock=%s,min_stock=%s,
                   unit=%s,barcode=%s,active=%s WHERE id=%s""",
                (prod.code, prod.name, prod.description, prod.category_id,
                 prod.supplier_id, prod.purchase_price, prod.sale_price,
                 prod.stock, prod.min_stock, prod.unit, prod.barcode,
                 int(prod.active), prod.id),
                commit=True
            )
            return prod.id
        return db.execute_query(
            """INSERT INTO products
               (code,name,description,category_id,supplier_id,purchase_price,
                sale_price,stock,min_stock,unit,barcode)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (prod.code, prod.name, prod.description, prod.category_id,
             prod.supplier_id, prod.purchase_price, prod.sale_price,
             prod.stock, prod.min_stock, prod.unit, prod.barcode),
            commit=True
        )

    def update_stock(self, product_id: int, new_stock: int) -> None:
        db.execute_query(
            "UPDATE products SET stock=%s WHERE id=%s",
            (new_stock, product_id), commit=True
        )

    def delete(self, entity_id: int) -> bool:
        db.execute_query(
            "UPDATE products SET active=0 WHERE id=%s", (entity_id,), commit=True
        )
        return True

    @staticmethod
    def _map(row: dict) -> Product:
        return Product(
            id=row["id"], code=row["code"], name=row["name"],
            description=row.get("description",""),
            category_id=row["category_id"], category_name=row.get("category_name",""),
            supplier_id=row.get("supplier_id"), supplier_name=row.get("supplier_name",""),
            purchase_price=float(row["purchase_price"]),
            sale_price=float(row["sale_price"]),
            stock=row["stock"], min_stock=row["min_stock"],
            unit=row.get("unit","unidad"), barcode=row.get("barcode",""),
            active=bool(row["active"]),
            created_at=row.get("created_at"), updated_at=row.get("updated_at")
        )


# ============================================================
# SALE REPOSITORY
# ============================================================
class SaleRepository(BaseRepository):

    def find_by_id(self, entity_id: int) -> Optional[Sale]:
        row = db.execute_query(
            """SELECT s.*, CONCAT(e.first_name,' ',e.last_name) AS employee_name
               FROM sales s JOIN employees e ON s.employee_id=e.id
               WHERE s.id=%s""",
            (entity_id,), fetch_one=True
        )
        if not row:
            return None
        sale = self._map(row)
        sale.details = self._get_details(entity_id)
        return sale

    def find_by_invoice(self, invoice_number: str) -> Optional[Sale]:
        row = db.execute_query(
            """SELECT s.*, CONCAT(e.first_name,' ',e.last_name) AS employee_name
               FROM sales s JOIN employees e ON s.employee_id=e.id
               WHERE s.invoice_number=%s""",
            (invoice_number,), fetch_one=True
        )
        if not row:
            return None
        sale = self._map(row)
        sale.details = self._get_details(row["id"])
        return sale

    def find_all(self) -> list[Sale]:
        rows = db.execute_query(
            """SELECT s.*, CONCAT(e.first_name,' ',e.last_name) AS employee_name
               FROM sales s JOIN employees e ON s.employee_id=e.id
               ORDER BY s.sold_at DESC""",
            fetch=True
        )
        return [self._map(r) for r in rows]

    def find_by_date_range(self, start: str, end: str) -> list[Sale]:
        rows = db.execute_query(
            """SELECT s.*, CONCAT(e.first_name,' ',e.last_name) AS employee_name
               FROM sales s JOIN employees e ON s.employee_id=e.id
               WHERE DATE(s.sold_at) BETWEEN %s AND %s
               ORDER BY s.sold_at DESC""",
            (start, end), fetch=True
        )
        return [self._map(r) for r in rows]

    def next_invoice_number(self) -> str:
        from config import INVOICE_PREFIX
        row = db.execute_query(
            "SELECT COUNT(*) AS total FROM sales", fetch_one=True
        )
        seq = (row["total"] if row else 0) + 1
        return f"{INVOICE_PREFIX}-{seq:06d}"

    def save(self, sale: Sale) -> int:
        """Guarda la venta y sus detalles en una transacción."""
        ops = [
            (
                """INSERT INTO sales
                   (invoice_number,employee_id,customer_id,subtotal,tax_amount,
                    total,paid_amount,change_amount,payment_method,status,notes,sold_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())""",
                (sale.invoice_number, sale.employee_id, sale.customer_id,
                 sale.subtotal, sale.tax_amount, sale.total, sale.paid_amount,
                 sale.change_amount, sale.payment_method, sale.status, sale.notes)
            )
        ]
        sale_id = db.execute_transaction(ops)
        # Insertar detalles
        for d in sale.details:
            db.execute_query(
                """INSERT INTO sale_details
                   (sale_id,product_id,product_name,unit_price,quantity,discount,subtotal)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (sale_id, d.product_id, d.product_name, d.unit_price,
                 d.quantity, d.discount, d.subtotal),
                commit=True
            )
        return sale_id

    def _get_details(self, sale_id: int) -> list[SaleDetail]:
        rows = db.execute_query(
            "SELECT * FROM sale_details WHERE sale_id=%s", (sale_id,), fetch=True
        )
        return [SaleDetail(
            id=r["id"], sale_id=r["sale_id"], product_id=r["product_id"],
            product_name=r["product_name"], unit_price=float(r["unit_price"]),
            quantity=r["quantity"], discount=float(r["discount"]),
            subtotal=float(r["subtotal"])
        ) for r in rows]

    def delete(self, entity_id: int) -> bool:
        db.execute_query(
            "UPDATE sales SET status='anulada' WHERE id=%s", (entity_id,), commit=True
        )
        return True

    @staticmethod
    def _map(row: dict) -> Sale:
        return Sale(
            id=row["id"], invoice_number=row["invoice_number"],
            employee_id=row["employee_id"], employee_name=row.get("employee_name",""),
            customer_id=row.get("customer_id"),
            subtotal=float(row["subtotal"]), tax_amount=float(row["tax_amount"]),
            total=float(row["total"]), paid_amount=float(row["paid_amount"]),
            change_amount=float(row["change_amount"]),
            payment_method=row["payment_method"], status=row["status"],
            notes=row.get("notes",""), sold_at=row.get("sold_at"),
            created_at=row.get("sold_at")
        )


# ============================================================
# PURCHASE REPOSITORY
# ============================================================
class PurchaseRepository(BaseRepository):

    def find_by_id(self, entity_id: int) -> Optional[Purchase]:
        row = db.execute_query(
            """SELECT p.*, s.name AS supplier_name
               FROM purchases p JOIN suppliers s ON p.supplier_id=s.id
               WHERE p.id=%s""",
            (entity_id,), fetch_one=True
        )
        if not row:
            return None
        purchase = self._map(row)
        purchase.details = self._get_details(entity_id)
        return purchase

    def find_all(self) -> list[Purchase]:
        rows = db.execute_query(
            """SELECT p.*, s.name AS supplier_name
               FROM purchases p JOIN suppliers s ON p.supplier_id=s.id
               ORDER BY p.purchased_at DESC""",
            fetch=True
        )
        return [self._map(r) for r in rows]

    def next_purchase_number(self) -> str:
        row = db.execute_query("SELECT COUNT(*) AS t FROM purchases", fetch_one=True)
        seq = (row["t"] if row else 0) + 1
        return f"CMP-{seq:06d}"

    def save(self, purchase: Purchase) -> int:
        ops = [(
            """INSERT INTO purchases
               (purchase_number,supplier_id,employee_id,total,status,notes,purchased_at)
               VALUES (%s,%s,%s,%s,%s,%s,NOW())""",
            (purchase.purchase_number, purchase.supplier_id, purchase.employee_id,
             purchase.total, purchase.status, purchase.notes)
        )]
        p_id = db.execute_transaction(ops)
        for d in purchase.details:
            db.execute_query(
                """INSERT INTO purchase_details (purchase_id,product_id,quantity,unit_cost,subtotal)
                   VALUES (%s,%s,%s,%s,%s)""",
                (p_id, d.product_id, d.quantity, d.unit_cost, d.subtotal),
                commit=True
            )
        return p_id

    def _get_details(self, purchase_id: int) -> list[PurchaseDetail]:
        rows = db.execute_query(
            """SELECT pd.*, p.name AS product_name
               FROM purchase_details pd JOIN products p ON pd.product_id=p.id
               WHERE pd.purchase_id=%s""",
            (purchase_id,), fetch=True
        )
        return [PurchaseDetail(
            id=r["id"], purchase_id=r["purchase_id"], product_id=r["product_id"],
            product_name=r.get("product_name",""), quantity=r["quantity"],
            unit_cost=float(r["unit_cost"]), subtotal=float(r["subtotal"])
        ) for r in rows]

    def delete(self, entity_id: int) -> bool:
        db.execute_query(
            "UPDATE purchases SET status='cancelada' WHERE id=%s", (entity_id,), commit=True
        )
        return True

    @staticmethod
    def _map(row: dict) -> Purchase:
        return Purchase(
            id=row["id"], purchase_number=row["purchase_number"],
            supplier_id=row["supplier_id"], supplier_name=row.get("supplier_name",""),
            employee_id=row["employee_id"], total=float(row["total"]),
            status=row["status"], notes=row.get("notes",""),
            purchased_at=row.get("purchased_at")
        )


# ============================================================
# REPORT REPOSITORY
# ============================================================
class ReportRepository:

    def daily_sales_summary(self, date: str) -> dict:
        row = db.execute_query(
            """SELECT COUNT(*) AS total_sales, COALESCE(SUM(total),0) AS revenue,
                      COALESCE(SUM(tax_amount),0) AS taxes
               FROM sales WHERE DATE(sold_at)=%s AND status='completada'""",
            (date,), fetch_one=True
        )
        return row or {}

    def sales_by_date_range(self, start: str, end: str) -> list[dict]:
        return db.execute_query(
            """SELECT DATE(sold_at) AS sale_date, COUNT(*) AS qty,
                      SUM(total) AS revenue
               FROM sales WHERE DATE(sold_at) BETWEEN %s AND %s
               AND status='completada'
               GROUP BY DATE(sold_at) ORDER BY sale_date""",
            (start, end), fetch=True
        ) or []

    def top_products(self, limit: int = 10, start: str = None, end: str = None) -> list[dict]:
        where = ""
        params: tuple = ()
        if start and end:
            where = " WHERE DATE(s.sold_at) BETWEEN %s AND %s AND s.status='completada'"
            params = (start, end)
        else:
            where = " WHERE s.status='completada'"
        return db.execute_query(
            f"""SELECT sd.product_name, SUM(sd.quantity) AS total_qty,
                       SUM(sd.subtotal) AS total_revenue
                FROM sale_details sd JOIN sales s ON sd.sale_id=s.id
                {where}
                GROUP BY sd.product_name ORDER BY total_qty DESC LIMIT %s""",
            (*params, limit), fetch=True
        ) or []

    def stock_report(self) -> list[dict]:
        return db.execute_query(
            """SELECT p.code, p.name, c.name AS category, p.stock,
                      p.min_stock, p.sale_price,
                      (p.stock * p.sale_price) AS stock_value,
                      IF(p.stock < p.min_stock, 'BAJO', 'OK') AS stock_status
               FROM products p JOIN categories c ON p.category_id=c.id
               WHERE p.active=1 ORDER BY p.stock ASC""",
            fetch=True
        ) or []

    def monthly_summary(self, year: int, month: int) -> dict:
        row = db.execute_query(
            """SELECT COUNT(*) AS total_sales, COALESCE(SUM(total),0) AS revenue,
                      COALESCE(AVG(total),0) AS avg_ticket
               FROM sales
               WHERE YEAR(sold_at)=%s AND MONTH(sold_at)=%s AND status='completada'""",
            (year, month), fetch_one=True
        )
        return row or {}

    def sales_by_employee(self, start: str, end: str) -> list[dict]:
        return db.execute_query(
            """SELECT CONCAT(e.first_name,' ',e.last_name) AS employee,
                      COUNT(*) AS total_sales, SUM(s.total) AS revenue
               FROM sales s JOIN employees e ON s.employee_id=e.id
               WHERE DATE(s.sold_at) BETWEEN %s AND %s AND s.status='completada'
               GROUP BY e.id ORDER BY revenue DESC""",
            (start, end), fetch=True
        ) or []


# ============================================================
# INVENTORY MOVEMENT REPOSITORY
# ============================================================
class InventoryMovementRepository:

    def save(self, mov: InventoryMovement) -> int:
        return db.execute_query(
            """INSERT INTO inventory_movements
               (product_id,employee_id,movement_type,quantity,stock_before,stock_after,notes,reference_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (mov.product_id, mov.employee_id, mov.movement_type, mov.quantity,
             mov.stock_before, mov.stock_after, mov.notes, mov.reference_id),
            commit=True
        )

    def find_by_product(self, product_id: int) -> list[dict]:
        return db.execute_query(
            """SELECT im.*, p.name AS product_name,
                      CONCAT(e.first_name,' ',e.last_name) AS employee_name
               FROM inventory_movements im
               JOIN products p ON im.product_id=p.id
               JOIN employees e ON im.employee_id=e.id
               WHERE im.product_id=%s ORDER BY im.created_at DESC""",
            (product_id,), fetch=True
        ) or []
