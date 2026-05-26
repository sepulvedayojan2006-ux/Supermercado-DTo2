# ============================================================
# models/__init__.py — Modelos de dominio (dataclasses)
# ============================================================
"""
Capa de modelos: representan entidades del negocio.
Aplican Encapsulamiento y Abstracción.
No dependen de la base de datos ni de la UI.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from abc import ABC, abstractmethod


# ============================================================
# BASE ABSTRACTA — Abstracción + Interface
# ============================================================
@dataclass
class BaseEntity(ABC):
    """Contrato común para todas las entidades del sistema."""
    id: Optional[int] = field(default=None, repr=False)
    created_at: Optional[datetime] = field(default=None, repr=False)
    updated_at: Optional[datetime] = field(default=None, repr=False)

    @abstractmethod
    def validate(self) -> list[str]:
        """Retorna lista de errores de validación. [] = válido."""

    def is_valid(self) -> bool:
        return len(self.validate()) == 0


# ============================================================
# CATEGORY
# ============================================================
@dataclass
class Category(BaseEntity):
    name: str = ""
    description: str = ""
    active: bool = True

    def validate(self) -> list[str]:
        errors = []
        if not self.name.strip():
            errors.append("El nombre de la categoría es requerido.")
        if len(self.name) > 80:
            errors.append("El nombre no puede superar 80 caracteres.")
        return errors

    def __str__(self) -> str:
        return self.name


# ============================================================
# EMPLOYEE / USER
# ============================================================
@dataclass
class Employee(BaseEntity):
    identification: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    email: str = ""
    role: str = "Cajero"
    password_hash: str = ""
    salary: float = 0.0
    active: bool = True

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def validate(self) -> list[str]:
        errors = []
        if not self.identification.strip():
            errors.append("La identificación es requerida.")
        if not self.first_name.strip():
            errors.append("El nombre es requerido.")
        if not self.last_name.strip():
            errors.append("El apellido es requerido.")
        if self.role not in ("Administrador", "Supervisor", "Cajero"):
            errors.append("Rol inválido.")
        if self.salary < 0:
            errors.append("El salario no puede ser negativo.")
        return errors

    def __str__(self) -> str:
        return f"{self.full_name} [{self.role}]"


# ============================================================
# SUPPLIER
# ============================================================
@dataclass
class Supplier(BaseEntity):
    name: str = ""
    nit: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    contact_person: str = ""
    active: bool = True

    def validate(self) -> list[str]:
        errors = []
        if not self.name.strip():
            errors.append("El nombre del proveedor es requerido.")
        if not self.nit.strip():
            errors.append("El NIT/identificación es requerido.")
        return errors

    def __str__(self) -> str:
        return f"{self.name} ({self.nit})"


# ============================================================
# PRODUCT
# ============================================================
@dataclass
class Product(BaseEntity):
    code: str = ""
    name: str = ""
    description: str = ""
    category_id: int = 0
    category_name: str = ""
    supplier_id: Optional[int] = None
    supplier_name: str = ""
    purchase_price: float = 0.0
    sale_price: float = 0.0
    stock: int = 0
    min_stock: int = 10
    unit: str = "unidad"
    barcode: str = ""
    active: bool = True

    @property
    def profit_margin(self) -> float:
        """Margen de ganancia en porcentaje."""
        if self.purchase_price <= 0:
            return 0.0
        return round(((self.sale_price - self.purchase_price) / self.purchase_price) * 100, 2)

    @property
    def is_low_stock(self) -> bool:
        return self.stock < self.min_stock

    def validate(self) -> list[str]:
        errors = []
        if not self.code.strip():
            errors.append("El código es requerido.")
        if not self.name.strip():
            errors.append("El nombre del producto es requerido.")
        if self.category_id <= 0:
            errors.append("Debe seleccionar una categoría.")
        if self.purchase_price < 0:
            errors.append("El precio de compra no puede ser negativo.")
        if self.sale_price < 0:
            errors.append("El precio de venta no puede ser negativo.")
        if self.stock < 0:
            errors.append("El stock no puede ser negativo.")
        return errors

    def __str__(self) -> str:
        return f"[{self.code}] {self.name}"


# ============================================================
# CART ITEM (Composición con SaleDetail)
# ============================================================
@dataclass
class CartItem:
    product: Product
    quantity: int = 1
    discount: float = 0.0

    @property
    def unit_price(self) -> float:
        return self.product.sale_price

    @property
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity * (1 - self.discount / 100), 2)

    def __str__(self) -> str:
        return f"{self.product.name} x{self.quantity} = ${self.subtotal:,.0f}"


# ============================================================
# SALE DETAIL
# ============================================================
@dataclass
class SaleDetail(BaseEntity):
    sale_id: int = 0
    product_id: int = 0
    product_name: str = ""
    unit_price: float = 0.0
    quantity: int = 1
    discount: float = 0.0
    subtotal: float = 0.0

    def validate(self) -> list[str]:
        errors = []
        if self.quantity <= 0:
            errors.append("La cantidad debe ser mayor a 0.")
        if self.unit_price < 0:
            errors.append("El precio unitario no puede ser negativo.")
        return errors


# ============================================================
# SALE (Factura de venta)
# ============================================================
@dataclass
class Sale(BaseEntity):
    invoice_number: str = ""
    employee_id: int = 0
    employee_name: str = ""
    customer_id: Optional[int] = None
    customer_name: str = "Consumidor Final"
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    paid_amount: float = 0.0
    change_amount: float = 0.0
    payment_method: str = "efectivo"
    status: str = "completada"
    notes: str = ""
    sold_at: Optional[datetime] = None
    details: List[SaleDetail] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.invoice_number:
            errors.append("El número de factura es requerido.")
        if self.employee_id <= 0:
            errors.append("Empleado no asignado.")
        if not self.details:
            errors.append("La venta debe tener al menos un producto.")
        if self.paid_amount < self.total:
            errors.append("El pago recibido es insuficiente.")
        return errors


# ============================================================
# PURCHASE DETAIL
# ============================================================
@dataclass
class PurchaseDetail(BaseEntity):
    purchase_id: int = 0
    product_id: int = 0
    product_name: str = ""
    quantity: int = 1
    unit_cost: float = 0.0
    subtotal: float = 0.0

    def validate(self) -> list[str]:
        errors = []
        if self.quantity <= 0:
            errors.append("Cantidad inválida.")
        return errors


# ============================================================
# PURCHASE (Compra a proveedor)
# ============================================================
@dataclass
class Purchase(BaseEntity):
    purchase_number: str = ""
    supplier_id: int = 0
    supplier_name: str = ""
    employee_id: int = 0
    total: float = 0.0
    status: str = "recibida"
    notes: str = ""
    purchased_at: Optional[datetime] = None
    details: List[PurchaseDetail] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if self.supplier_id <= 0:
            errors.append("Debe seleccionar un proveedor.")
        if not self.details:
            errors.append("La compra debe tener al menos un producto.")
        return errors


# ============================================================
# CUSTOMER
# ============================================================
@dataclass
class Customer(BaseEntity):
    identification: str = ""
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.identification.strip():
            errors.append("La identificación del cliente es requerida.")
        if not self.name.strip():
            errors.append("El nombre del cliente es requerido.")
        return errors

    def __str__(self) -> str:
        return f"{self.name} ({self.identification})"


# ============================================================
# INVENTORY MOVEMENT
# ============================================================
@dataclass
class InventoryMovement(BaseEntity):
    product_id: int = 0
    product_name: str = ""
    employee_id: int = 0
    movement_type: str = "ajuste"
    quantity: int = 0
    stock_before: int = 0
    stock_after: int = 0
    notes: str = ""
    reference_id: Optional[int] = None

    def validate(self) -> list[str]:
        errors = []
        if self.quantity == 0:
            errors.append("La cantidad del movimiento no puede ser 0.")
        return errors
