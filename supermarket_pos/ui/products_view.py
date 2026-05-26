# ============================================================
# ui/products_view.py — Gestión de Productos
# ============================================================

import tkinter as tk
from tkinter import ttk

from config import (THEME_PRIMARY, THEME_SECONDARY, THEME_BG, THEME_WHITE,
                    THEME_TEXT, FONT_FAMILY, ROLE_ADMIN, ROLE_SUPERVISOR)
from services import AuthService, ProductService, SupplierService
from models import Product
from ui.components import (DataTable, btn, SearchBar, FormDialog,
                            show_error, show_info, confirm)


# ============================================================
# PRODUCT FORM DIALOG
# ============================================================
class ProductFormDialog(FormDialog):

    def __init__(self, parent, product: Product = None,
                 categories=None, suppliers=None):
        self._prod    = product or Product()
        self._cats    = categories or []
        self._sups    = suppliers or []
        self._is_edit = product is not None
        super().__init__(parent,
                         title="Editar Producto" if self._is_edit else "Nuevo Producto",
                         width=520, height=580)

    def _build_ui(self) -> None:
        self.configure(bg=THEME_BG)
        ttk.Label(self, text="📦 Datos del Producto",
                  font=(FONT_FAMILY, 13, "bold"),
                  foreground=THEME_PRIMARY, background=THEME_BG).pack(pady=(16, 8))

        form = tk.Frame(self, bg=THEME_BG)
        form.pack(fill="both", expand=True, padx=24)
        form.columnconfigure(1, weight=1)

        self._code_var     = self._field(form, "Código *",          0)
        self._name_var     = self._field(form, "Nombre *",          1)
        self._barcode_var  = self._field(form, "Código de barras",  2)

        # Categoría (combo)
        cat_names = [c.name for c in self._cats]
        self._cat_var = self._field(form, "Categoría *", 3, widget_type="combo",
                                    values=cat_names)

        self._unit_var     = self._field(form, "Unidad",            4,
                                          var=tk.StringVar(value="unidad"))
        self._pprice_var   = self._field(form, "Precio compra *",   5,
                                          widget_type="spinbox")
        self._sprice_var   = self._field(form, "Precio venta *",    6,
                                          widget_type="spinbox")
        self._stock_var    = self._field(form, "Stock inicial",     7,
                                          widget_type="spinbox")
        self._min_stock_var = self._field(form, "Stock mínimo",     8,
                                           var=tk.StringVar(value="10"),
                                           widget_type="spinbox")

        # Proveedor (combo opcional)
        sup_names = ["(Ninguno)"] + [s.name for s in self._sups]
        self._sup_var = self._field(form, "Proveedor",  9, widget_type="combo",
                                    values=sup_names)

        # Margen (solo lectura, se actualiza automáticamente)
        self._margin_var = tk.StringVar(value="0%")
        ttk.Label(form, text="Margen estimado:", background=THEME_BG).grid(
            row=10, column=0, sticky="w", padx=8, pady=4)
        ttk.Label(form, textvariable=self._margin_var,
                  background=THEME_BG, foreground=THEME_PRIMARY,
                  font=(FONT_FAMILY, 10, "bold")).grid(
            row=10, column=1, sticky="w", padx=8)

        self._pprice_var.trace_add("write", lambda *_: self._calc_margin())
        self._sprice_var.trace_add("write", lambda *_: self._calc_margin())

        # Pre-cargar si es edición
        if self._is_edit:
            p = self._prod
            self._code_var.set(p.code)
            self._name_var.set(p.name)
            self._barcode_var.set(p.barcode)
            self._unit_var.set(p.unit)
            self._pprice_var.set(str(p.purchase_price))
            self._sprice_var.set(str(p.sale_price))
            self._stock_var.set(str(p.stock))
            self._min_stock_var.set(str(p.min_stock))
            # Categoría
            for c in self._cats:
                if c.id == p.category_id:
                    self._cat_var.set(c.name)
                    break
            # Proveedor
            if p.supplier_id:
                for s in self._sups:
                    if s.id == p.supplier_id:
                        self._sup_var.set(s.name)
                        break

        # Botones
        bf = tk.Frame(self, bg=THEME_BG)
        bf.pack(fill="x", padx=24, pady=12)
        btn(bf, "💾 Guardar", self.ok,    style="Primary.TButton").pack(side="left", padx=4)
        btn(bf, "✖ Cancelar", self.cancel, style="Danger.TButton").pack(side="left", padx=4)

    def _calc_margin(self) -> None:
        try:
            pp = float(self._pprice_var.get() or 0)
            sp = float(self._sprice_var.get() or 0)
            if pp > 0:
                margin = ((sp - pp) / pp) * 100
                self._margin_var.set(f"{margin:.1f}%")
        except ValueError:
            pass

    def ok(self) -> None:
        p = self._prod
        p.code         = self._code_var.get().strip()
        p.name         = self._name_var.get().strip()
        p.barcode      = self._barcode_var.get().strip()
        p.unit         = self._unit_var.get().strip() or "unidad"

        # Categoría
        cat_name = self._cat_var.get()
        for c in self._cats:
            if c.name == cat_name:
                p.category_id = c.id
                break

        # Proveedor
        sup_name = self._sup_var.get()
        p.supplier_id = None
        for s in self._sups:
            if s.name == sup_name:
                p.supplier_id = s.id
                break

        try:
            p.purchase_price = float(self._pprice_var.get() or 0)
            p.sale_price     = float(self._sprice_var.get() or 0)
            p.stock          = int(self._stock_var.get() or 0)
            p.min_stock      = int(self._min_stock_var.get() or 10)
        except ValueError:
            show_error(self, "Los valores numéricos son inválidos.")
            return

        self.result = p
        self.destroy()


# ============================================================
# PRODUCTS VIEW
# ============================================================
class ProductsView(tk.Frame):

    def __init__(self, parent, auth: AuthService):
        super().__init__(parent, bg=THEME_BG)
        self._auth     = auth
        self._svc      = ProductService()
        self._sup_svc  = SupplierService()
        self._can_edit = auth.current_user.role in (ROLE_ADMIN, ROLE_SUPERVISOR)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        # Encabezado
        hdr = tk.Frame(self, bg=THEME_PRIMARY, height=46)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📦  Gestión de Productos",
                 bg=THEME_PRIMARY, fg="white",
                 font=(FONT_FAMILY, 14, "bold")).pack(side="left", padx=16, pady=10)

        # Toolbar
        tb = tk.Frame(self, bg=THEME_BG)
        tb.pack(fill="x", padx=10, pady=6)
        SearchBar(tb, "Buscar producto...", on_search=self._search).pack(side="left")
        if self._can_edit:
            btn(tb, "➕ Nuevo",   self._new,    style="Primary.TButton").pack(side="right", padx=3)
            btn(tb, "✏ Editar",   self._edit,   style="Secondary.TButton").pack(side="right", padx=3)
            btn(tb, "🗑 Eliminar", self._delete, style="Danger.TButton").pack(side="right", padx=3)

        # Tabla
        self._table = DataTable(self, columns=[
            ("code",     "Código",      90,  "w"),
            ("name",     "Nombre",      200, "w"),
            ("category", "Categoría",   120, "w"),
            ("pprice",   "P. Compra",   100, "e"),
            ("sprice",   "P. Venta",    100, "e"),
            ("margin",   "Margen",      70,  "center"),
            ("stock",    "Stock",       60,  "center"),
            ("unit",     "Unidad",      70,  "center"),
            ("status",   "Estado",      80,  "center"),
        ])
        self._table.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self._table.bind("<Double-1>", lambda _: self._edit())

    def _load(self, term: str = "") -> None:
        prods = self._svc.search(term) if term else self._svc.list_all()
        self._items = prods
        rows, tags = [], []
        for p in prods:
            rows.append((
                p.code, p.name, p.category_name,
                f"$ {p.purchase_price:,.0f}",
                f"$ {p.sale_price:,.0f}",
                f"{p.profit_margin:.1f}%",
                p.stock, p.unit,
                "✅ Activo" if p.active else "❌ Inactivo"
            ))
            tag = "low" if p.is_low_stock else ("odd" if len(rows) % 2 == 0 else "even")
            tags.append(tag)
        self._table.load(rows, tags)

    def _search(self, term: str) -> None:
        self._load(term)

    def _selected_product(self):
        row = self._table.selected_row()
        if row is None:
            show_error(self, "Selecciona un producto.")
            return None
        code = row[0]
        return self._svc.find_by_code(code)

    def _new(self) -> None:
        cats = self._svc.categories()
        sups = self._sup_svc.list_all()
        d = ProductFormDialog(self, categories=cats, suppliers=sups)
        if d.result:
            try:
                self._svc.create(d.result)
                show_info(self, "Producto creado correctamente.")
                self._load()
            except ValueError as e:
                show_error(self, str(e))

    def _edit(self) -> None:
        prod = self._selected_product()
        if prod is None:
            return
        cats = self._svc.categories()
        sups = self._sup_svc.list_all()
        d = ProductFormDialog(self, product=prod, categories=cats, suppliers=sups)
        if d.result:
            try:
                self._svc.update(d.result)
                show_info(self, "Producto actualizado correctamente.")
                self._load()
            except ValueError as e:
                show_error(self, str(e))

    def _delete(self) -> None:
        prod = self._selected_product()
        if prod is None:
            return
        if confirm(self, "Eliminar producto",
                   f"¿Eliminar '{prod.name}'? Esta acción no se puede deshacer."):
            self._svc.delete(prod.id)
            show_info(self, "Producto eliminado.")
            self._load()
