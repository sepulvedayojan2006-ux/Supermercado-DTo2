# ============================================================
# ui/suppliers_view.py — Gestión de Proveedores
# ============================================================

import tkinter as tk
from tkinter import ttk

from config import (THEME_PRIMARY, THEME_BG, FONT_FAMILY, ROLE_ADMIN, ROLE_SUPERVISOR)
from services import AuthService, SupplierService
from models import Supplier
from ui.components import (DataTable, btn, FormDialog,
                            show_error, show_info, confirm)


# ============================================================
# SUPPLIER FORM DIALOG
# ============================================================
class SupplierFormDialog(FormDialog):

    def __init__(self, parent, supplier: Supplier = None):
        self._sup     = supplier or Supplier()
        self._is_edit = supplier is not None
        super().__init__(parent,
                         title="Editar Proveedor" if self._is_edit else "Nuevo Proveedor",
                         width=480, height=480)

    def _build_ui(self) -> None:
        self.configure(bg=THEME_BG)
        ttk.Label(self, text="🚚 Datos del Proveedor",
                  font=(FONT_FAMILY, 13, "bold"),
                  foreground=THEME_PRIMARY, background=THEME_BG).pack(pady=(16, 8))

        form = tk.Frame(self, bg=THEME_BG)
        form.pack(fill="both", expand=True, padx=24)
        form.columnconfigure(1, weight=1)

        self._name_var    = self._field(form, "Nombre / Razón social *", 0)
        self._nit_var     = self._field(form, "NIT / Identificación *",  1)
        self._contact_var = self._field(form, "Persona de contacto",      2)
        self._phone_var   = self._field(form, "Teléfono / Celular",       3)
        self._email_var   = self._field(form, "Correo electrónico",       4)
        self._addr_var    = self._field(form, "Dirección",                5)

        if self._is_edit:
            s = self._sup
            self._name_var.set(s.name)
            self._nit_var.set(s.nit)
            self._contact_var.set(s.contact_person)
            self._phone_var.set(s.phone)
            self._email_var.set(s.email)
            self._addr_var.set(s.address)

        bf = tk.Frame(self, bg=THEME_BG)
        bf.pack(fill="x", padx=24, pady=12)
        btn(bf, "💾 Guardar",  self.ok,     style="Primary.TButton").pack(side="left", padx=4)
        btn(bf, "✖ Cancelar", self.cancel, style="Danger.TButton").pack(side="left",  padx=4)

    def ok(self) -> None:
        s = self._sup
        s.name           = self._name_var.get().strip()
        s.nit            = self._nit_var.get().strip()
        s.contact_person = self._contact_var.get().strip()
        s.phone          = self._phone_var.get().strip()
        s.email          = self._email_var.get().strip()
        s.address        = self._addr_var.get().strip()

        errors = s.validate()
        if errors:
            show_error(self, "\n".join(errors))
            return
        self.result = s
        self.destroy()


# ============================================================
# SUPPLIERS VIEW
# ============================================================
class SuppliersView(tk.Frame):

    def __init__(self, parent, auth: AuthService):
        super().__init__(parent, bg=THEME_BG)
        self._auth    = auth
        self._svc     = SupplierService()
        self._can_edit = auth.current_user.role in (ROLE_ADMIN, ROLE_SUPERVISOR)
        self._build_ui()
        self._load()

    # ----------------------------------------------------------
    def _build_ui(self) -> None:
        hdr = tk.Frame(self, bg=THEME_PRIMARY, height=46)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🚚  Gestión de Proveedores",
                 bg=THEME_PRIMARY, fg="white",
                 font=(FONT_FAMILY, 14, "bold")).pack(side="left", padx=16, pady=10)

        tb = tk.Frame(self, bg=THEME_BG)
        tb.pack(fill="x", padx=10, pady=6)
        if self._can_edit:
            btn(tb, "➕ Nuevo",    self._new,    style="Primary.TButton").pack(side="left",  padx=3)
            btn(tb, "✏ Editar",   self._edit,   style="Secondary.TButton").pack(side="left", padx=3)
            btn(tb, "🗑 Eliminar", self._delete, style="Danger.TButton").pack(side="right",  padx=3)

        # Tabla de proveedores
        self._table = DataTable(self, columns=[
            ("id",      "ID",          55,  "center"),
            ("name",    "Nombre",      200, "w"),
            ("nit",     "NIT",         120, "w"),
            ("contact", "Contacto",    150, "w"),
            ("phone",   "Teléfono",    110, "center"),
            ("email",   "Correo",      200, "w"),
            ("address", "Dirección",   200, "w"),
            ("status",  "Estado",      80,  "center"),
        ])
        self._table.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self._table.bind("<Double-1>", lambda _: self._edit())

        # Panel inferior: productos vinculados al proveedor seleccionado
        detail_frame = ttk.LabelFrame(self, text=" Productos asociados al proveedor seleccionado ")
        detail_frame.pack(fill="x", padx=10, pady=(0, 8))
        self._detail_table = DataTable(detail_frame, columns=[
            ("code",  "Código",    90,  "w"),
            ("name",  "Producto", 200,  "w"),
            ("stock", "Stock",     70,  "center"),
            ("pprice","P.Compra", 110,  "e"),
            ("sprice","P.Venta",  110,  "e"),
        ], height=5)
        self._detail_table.pack(fill="x", padx=8, pady=6)
        self._table.bind("<<TreeviewSelect>>", lambda _: self._on_select())

    # ----------------------------------------------------------
    def _load(self) -> None:
        sups = self._svc.list_all()
        self._items = sups
        rows, tags = [], []
        for s in sups:
            rows.append((
                s.id, s.name, s.nit, s.contact_person,
                s.phone, s.email, s.address,
                "✅ Activo" if s.active else "❌ Inactivo"
            ))
            tags.append("even" if len(rows) % 2 == 0 else "odd")
        self._table.load(rows, tags)

    def _on_select(self) -> None:
        """Carga los productos asociados al proveedor seleccionado."""
        row = self._table.selected_row()
        if row is None:
            return
        sup_id = int(row[0])
        from repositories import ProductRepository
        repo = ProductRepository()
        prods = [p for p in repo.find_active() if p.supplier_id == sup_id]
        rows = [(p.code, p.name, p.stock,
                 f"$ {p.purchase_price:,.0f}", f"$ {p.sale_price:,.0f}")
                for p in prods]
        self._detail_table.load(rows)

    # ----------------------------------------------------------
    def _selected_sup(self) -> Supplier | None:
        row = self._table.selected_row()
        if row is None:
            show_error(self, "Selecciona un proveedor.")
            return None
        return self._svc.find(int(row[0]))

    def _new(self) -> None:
        d = SupplierFormDialog(self)
        if d.result:
            try:
                self._svc.create(d.result)
                show_info(self, "Proveedor registrado correctamente.")
                self._load()
            except ValueError as e:
                show_error(self, str(e))

    def _edit(self) -> None:
        sup = self._selected_sup()
        if sup is None:
            return
        d = SupplierFormDialog(self, supplier=sup)
        if d.result:
            try:
                self._svc.update(d.result)
                show_info(self, "Proveedor actualizado correctamente.")
                self._load()
            except ValueError as e:
                show_error(self, str(e))

    def _delete(self) -> None:
        sup = self._selected_sup()
        if sup is None:
            return
        if confirm(self, "Eliminar proveedor",
                   f"¿Eliminar a '{sup.name}'?\nLos productos vinculados quedarán sin proveedor."):
            self._svc.delete(sup.id)
            show_info(self, "Proveedor eliminado.")
            self._load()
