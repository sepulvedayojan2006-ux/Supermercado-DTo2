# ============================================================
# services/__init__.py — Capa de Lógica de Negocio
# ============================================================
"""
Servicios: orquestan casos de uso completos.
Separan la lógica de negocio de la UI y de la BD.
Aplican principios SOLID: SRP, OCP, DIP.
"""

from __future__ import annotations
import bcrypt
from datetime import datetime
from typing import Optional

from config import BCRYPT_ROUNDS, TAX_RATE, LOW_STOCK_THRESHOLD
from models import (
    Employee, Product, Sale, SaleDetail, CartItem,
    Supplier, Category, Purchase, PurchaseDetail, InventoryMovement
)
from repositories import (
    EmployeeRepository, ProductRepository, SaleRepository,
    SupplierRepository, CategoryRepository, PurchaseRepository,
    ReportRepository, InventoryMovementRepository
)


# ============================================================
# AUTH SERVICE
# ============================================================
class AuthService:
    """Gestiona autenticación y sesiones."""

    def __init__(self):
        self._repo = EmployeeRepository()
        self._current_user: Optional[Employee] = None

    # --- Singleton de sesión activa ---
    @property
    def current_user(self) -> Optional[Employee]:
        return self._current_user

    def login(self, identification: str, password: str) -> Employee:
        """
        Autentica un usuario.
        Raises ValueError si las credenciales son inválidas.
        """
        emp = self._repo.find_by_identification(identification)
        if emp is None:
            raise ValueError("Identificación no encontrada.")
        if not emp.active:
            raise ValueError("Este usuario está desactivado.")
        if not self._verify_password(password, emp.password_hash):
            raise ValueError("Contraseña incorrecta.")
        self._current_user = emp
        return emp

    def logout(self) -> None:
        self._current_user = None

    def is_admin(self) -> bool:
        return self._current_user is not None and self._current_user.role == "Administrador"

    def is_supervisor_or_above(self) -> bool:
        return self._current_user is not None and \
               self._current_user.role in ("Administrador", "Supervisor")

    @staticmethod
    def hash_password(plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()

    @staticmethod
    def _verify_password(plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode(), hashed.encode())
        except Exception:
            return False


# ============================================================
# EMPLOYEE SERVICE
# ============================================================
class EmployeeService:

    def __init__(self):
        self._repo = EmployeeRepository()

    def list_all(self) -> list[Employee]:
        return self._repo.find_active()

    def find(self, emp_id: int) -> Optional[Employee]:
        return self._repo.find_by_id(emp_id)

    def create(self, emp: Employee, plain_password: str) -> int:
        """Crea un nuevo empleado con contraseña hasheada."""
        errors = emp.validate()
        if errors:
            raise ValueError("\n".join(errors))
        if not plain_password or len(plain_password) < 6:
            raise ValueError("La contraseña debe tener mínimo 6 caracteres.")
        # Verificar identificación única
        existing = self._repo.find_by_identification(emp.identification)
        if existing:
            raise ValueError(f"Ya existe un empleado con la identificación {emp.identification}.")
        emp.password_hash = AuthService.hash_password(plain_password)
        return self._repo.save(emp)

    def update(self, emp: Employee) -> int:
        errors = emp.validate()
        if errors:
            raise ValueError("\n".join(errors))
        # Verificar duplicado (excluir el mismo)
        existing = self._repo.find_by_identification(emp.identification)
        if existing and existing.id != emp.id:
            raise ValueError(f"La identificación {emp.identification} ya está en uso.")
        return self._repo.save(emp)

    def change_password(self, emp_id: int, new_password: str) -> None:
        if len(new_password) < 6:
            raise ValueError("La contraseña debe tener mínimo 6 caracteres.")
        hashed = AuthService.hash_password(new_password)
        self._repo.update_password(emp_id, hashed)

    def deactivate(self, emp_id: int) -> None:
        emp = self._repo.find_by_id(emp_id)
        if emp is None:
            raise ValueError("Empleado no encontrado.")
        emp.active = False
        self._repo.save(emp)

    def activate(self, emp_id: int) -> None:
        emp = self._repo.find_by_id(emp_id)
        if emp is None:
            raise ValueError("Empleado no encontrado.")
        emp.active = True
        self._repo.save(emp)

    def delete(self, emp_id: int) -> None:
        self._repo.delete(emp_id)


# ============================================================
# PRODUCT SERVICE
# ============================================================
class ProductService:

    def __init__(self):
        self._repo = ProductRepository()
        self._cat_repo = CategoryRepository()
        self._mov_repo = InventoryMovementRepository()

    def list_all(self) -> list[Product]:
        return self._repo.find_active()

    def search(self, term: str) -> list[Product]:
        return self._repo.search(term)

    def find(self, product_id: int) -> Optional[Product]:
        return self._repo.find_by_id(product_id)

    def find_by_code(self, code: str) -> Optional[Product]:
        return self._repo.find_by_code(code)

    def low_stock(self) -> list[Product]:
        return self._repo.find_low_stock()

    def categories(self) -> list[Category]:
        return self._cat_repo.find_active()

    def create(self, prod: Product) -> int:
        errors = prod.validate()
        if errors:
            raise ValueError("\n".join(errors))
        # Verificar duplicado entre productos ACTIVOS únicamente
        existing = self._repo.find_by_code(prod.code)  # ya filtra active=1
        if existing:
            raise ValueError(f"Ya existe un producto activo con código '{prod.code}'.")
        return self._repo.save(prod)

    def update(self, prod: Product) -> int:
        errors = prod.validate()
        if errors:
            raise ValueError("\n".join(errors))
        # Al editar, verificar que el código no lo use OTRO producto activo
        existing = self._repo.find_by_code(prod.code)
        if existing and existing.id != prod.id:
            raise ValueError(f"El código '{prod.code}' ya está en uso.")
        return self._repo.save(prod)

    def delete(self, product_id: int) -> None:
        self._repo.delete(product_id)

    def adjust_stock(self, product_id: int, delta: int,
                     movement_type: str, employee_id: int, notes: str = "") -> None:
        """Ajusta stock y registra movimiento."""
        prod = self._repo.find_by_id(product_id)
        if prod is None:
            raise ValueError("Producto no encontrado.")
        new_stock = prod.stock + delta
        if new_stock < 0:
            raise ValueError(f"Stock insuficiente. Disponible: {prod.stock}")
        mov = InventoryMovement(
            product_id=product_id,
            employee_id=employee_id,
            movement_type=movement_type,
            quantity=abs(delta),
            stock_before=prod.stock,
            stock_after=new_stock,
            notes=notes
        )
        self._mov_repo.save(mov)
        self._repo.update_stock(product_id, new_stock)


# ============================================================
# CART SERVICE (Composición)
# ============================================================
class CartService:
    """Carrito de compras para el módulo de ventas."""

    def __init__(self):
        self._items: list[CartItem] = []

    def add_item(self, product: Product, quantity: int = 1) -> None:
        """Agrega o incrementa un producto en el carrito."""
        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        # Buscar si ya existe
        for item in self._items:
            if item.product.id == product.id:
                new_qty = item.quantity + quantity
                if new_qty > product.stock:
                    raise ValueError(f"Stock insuficiente. Disponible: {product.stock}")
                item.quantity = new_qty
                return
        if quantity > product.stock:
            raise ValueError(f"Stock insuficiente. Disponible: {product.stock}")
        self._items.append(CartItem(product=product, quantity=quantity))

    def remove_item(self, product_id: int) -> None:
        self._items = [i for i in self._items if i.product.id != product_id]

    def update_quantity(self, product_id: int, quantity: int) -> None:
        for item in self._items:
            if item.product.id == product_id:
                if quantity <= 0:
                    self.remove_item(product_id)
                    return
                if quantity > item.product.stock:
                    raise ValueError(f"Stock insuficiente. Disponible: {item.product.stock}")
                item.quantity = quantity
                return

    def clear(self) -> None:
        self._items.clear()

    @property
    def items(self) -> list[CartItem]:
        return list(self._items)

    @property
    def item_count(self) -> int:
        return sum(i.quantity for i in self._items)

    @property
    def subtotal(self) -> float:
        return round(sum(i.subtotal for i in self._items), 2)

    @property
    def tax(self) -> float:
        return round(self.subtotal * TAX_RATE, 2)

    @property
    def total(self) -> float:
        return round(self.subtotal + self.tax, 2)

    def calculate_change(self, paid: float) -> float:
        return round(paid - self.total, 2)

    def is_empty(self) -> bool:
        return len(self._items) == 0


# ============================================================
# SALE SERVICE
# ============================================================
class SaleService:

    def __init__(self):
        self._repo = SaleRepository()
        self._prod_repo = ProductRepository()
        self._mov_repo = InventoryMovementRepository()

    def list_all(self) -> list[Sale]:
        return self._repo.find_all()

    def find(self, sale_id: int) -> Optional[Sale]:
        return self._repo.find_by_id(sale_id)

    def checkout(self, cart: CartService, employee_id: int,
                 paid_amount: float, payment_method: str = "efectivo",
                 customer_id: Optional[int] = None) -> Sale:
        """
        Procesa la venta completa:
        1. Valida el carrito
        2. Verifica stock
        3. Genera factura
        4. Descuenta inventario
        5. Registra movimientos
        """
        if cart.is_empty():
            raise ValueError("El carrito está vacío.")
        if paid_amount < cart.total:
            raise ValueError(
                f"Pago insuficiente. Total: ${cart.total:,.0f}  Recibido: ${paid_amount:,.0f}"
            )
        # Crear objeto Sale
        sale = Sale(
            invoice_number=self._repo.next_invoice_number(),
            employee_id=employee_id,
            customer_id=customer_id,
            subtotal=cart.subtotal,
            tax_amount=cart.tax,
            total=cart.total,
            paid_amount=paid_amount,
            change_amount=cart.calculate_change(paid_amount),
            payment_method=payment_method,
            status="completada",
            sold_at=datetime.now()
        )
        # Construir detalles
        for ci in cart.items:
            sale.details.append(SaleDetail(
                product_id=ci.product.id,
                product_name=ci.product.name,
                unit_price=ci.unit_price,
                quantity=ci.quantity,
                discount=ci.discount,
                subtotal=ci.subtotal
            ))
        # Guardar en BD (transacción)
        sale_id = self._repo.save(sale)
        sale.id = sale_id
        # Descontar stock y registrar movimiento
        for ci in cart.items:
            prod = self._prod_repo.find_by_id(ci.product.id)
            new_stock = prod.stock - ci.quantity
            mov = InventoryMovement(
                product_id=ci.product.id,
                employee_id=employee_id,
                movement_type="venta",
                quantity=ci.quantity,
                stock_before=prod.stock,
                stock_after=max(0, new_stock),
                notes=f"Venta {sale.invoice_number}",
                reference_id=sale_id
            )
            self._mov_repo.save(mov)
            self._prod_repo.update_stock(ci.product.id, max(0, new_stock))
        return sale

    def cancel_sale(self, sale_id: int, employee_id: int) -> None:
        """Anula una venta y devuelve el stock."""
        sale = self._repo.find_by_id(sale_id)
        if sale is None:
            raise ValueError("Venta no encontrada.")
        if sale.status == "anulada":
            raise ValueError("Esta venta ya fue anulada.")
        # Restaurar stock
        for d in sale.details:
            prod = self._prod_repo.find_by_id(d.product_id)
            new_stock = prod.stock + d.quantity
            mov = InventoryMovement(
                product_id=d.product_id,
                employee_id=employee_id,
                movement_type="devolucion",
                quantity=d.quantity,
                stock_before=prod.stock,
                stock_after=new_stock,
                notes=f"Anulación {sale.invoice_number}",
                reference_id=sale_id
            )
            self._mov_repo.save(mov)
            self._prod_repo.update_stock(d.product_id, new_stock)
        self._repo.delete(sale_id)


# ============================================================
# SUPPLIER SERVICE
# ============================================================
class SupplierService:

    def __init__(self):
        self._repo = SupplierRepository()

    def list_all(self) -> list[Supplier]:
        return self._repo.find_active()

    def find(self, sup_id: int) -> Optional[Supplier]:
        return self._repo.find_by_id(sup_id)

    def create(self, sup: Supplier) -> int:
        errors = sup.validate()
        if errors:
            raise ValueError("\n".join(errors))
        return self._repo.save(sup)

    def update(self, sup: Supplier) -> int:
        errors = sup.validate()
        if errors:
            raise ValueError("\n".join(errors))
        return self._repo.save(sup)

    def delete(self, sup_id: int) -> None:
        self._repo.delete(sup_id)


# ============================================================
# PURCHASE SERVICE
# ============================================================
class PurchaseService:

    def __init__(self):
        self._repo = PurchaseRepository()
        self._prod_repo = ProductRepository()
        self._mov_repo = InventoryMovementRepository()

    def list_all(self) -> list[Purchase]:
        return self._repo.find_all()

    def receive_purchase(self, purchase: Purchase) -> int:
        """Registra una compra y actualiza el inventario."""
        errors = purchase.validate()
        if errors:
            raise ValueError("\n".join(errors))
        purchase.purchase_number = self._repo.next_purchase_number()
        purchase.total = sum(d.subtotal for d in purchase.details)
        p_id = self._repo.save(purchase)
        # Actualizar stock
        for d in purchase.details:
            prod = self._prod_repo.find_by_id(d.product_id)
            new_stock = prod.stock + d.quantity
            # Actualizar precio de compra
            prod.purchase_price = d.unit_cost
            self._prod_repo.save(prod)
            mov = InventoryMovement(
                product_id=d.product_id,
                employee_id=purchase.employee_id,
                movement_type="compra",
                quantity=d.quantity,
                stock_before=prod.stock,
                stock_after=new_stock,
                notes=f"Compra {purchase.purchase_number}",
                reference_id=p_id
            )
            self._mov_repo.save(mov)
            self._prod_repo.update_stock(d.product_id, new_stock)
        return p_id


# ============================================================
# REPORT SERVICE
# ============================================================
class ReportService:

    def __init__(self):
        self._repo = ReportRepository()
        self._prod_repo = ProductRepository()

    def daily_summary(self, date: str) -> dict:
        return self._repo.daily_sales_summary(date)

    def sales_by_range(self, start: str, end: str) -> list[dict]:
        return self._repo.sales_by_date_range(start, end)

    def top_products(self, limit: int = 10, start: str = None, end: str = None) -> list[dict]:
        return self._repo.top_products(limit, start, end)

    def stock_report(self) -> list[dict]:
        return self._repo.stock_report()

    def low_stock_alert(self) -> list[Product]:
        return self._prod_repo.find_low_stock()

    def monthly(self, year: int, month: int) -> dict:
        return self._repo.monthly_summary(year, month)

    def by_employee(self, start: str, end: str) -> list[dict]:
        return self._repo.sales_by_employee(start, end)
