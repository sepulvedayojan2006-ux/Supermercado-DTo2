# ============================================================
# ui/inventory_view.py — Inventario y Movimientos de Stock
# ============================================================

import tkinter as tk
from tkinter import ttk

from config import (THEME_PRIMARY, THEME_SECONDARY, THEME_BG, THEME_WHITE,
                    THEME_DANGER, THEME_WARNING, THEME_TEXT, FONT_FAMILY,
                    LOW_STOCK_THRESHOLD, ROLE_ADMIN, ROLE_SUPERVISOR)
from services import AuthService, ProductService
from ui.components import (DataTable, btn, FormDialog,
                            show_error, show_info, confirm)


# ============================================================
# STOCK ADJUSTMENT DIALOG
# ============================================================
class StockAdjustDialog(FormDialog):
    """Diálogo para ajustar manualmente el stock de un producto."""

    def __init__(self, parent, product):
        self._prod = product
        super().__init__(parent, title=f"Ajustar Stock — {product.name}",
                         width=400, height=320)

    def _build_ui(self) -> None:
        self.configure(bg=THEME_BG)

        info = tk.Frame(self, bg=THEME_WHITE, relief="groove", bd=1)
        info.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(info, text=f"Producto: {self._prod.name}",
                 bg=THEME_WHITE, font=(FONT_FAMILY, 10, "bold")).pack(anchor="w", padx=10, pady=4)
        tk.Label(info, text=f"Código: {self._prod.code}  |  Stock actual: {self._prod.stock}",
                 bg=THEME_WHITE, font=(FONT_FAMILY, 10),
                 fg=THEME_DANGER if self._prod.is_low_stock else THEME_TEXT).pack(
            anchor="w", padx=10, pady=(0, 6))

        form = tk.Frame(self, bg=THEME_BG)
        form.pack(fill="x", padx=20)
        form.columnconfigure(1, weight=1)

        self._type_var = self._field(form, "Tipo de ajuste *", 0,
                                      widget_type="combo",
                                      values=["ajuste", "devolucion"])
        self._qty_var  = self._field(form, "Cantidad *",       1, widget_type="spinbox")
        self._note_var = self._field(form, "Nota / Motivo",    2)

        self._type_var.set("ajuste")

        bf = tk.Frame(self, bg=THEME_BG)
        bf.pack(fill="x", padx=20, pady=12)
        btn(bf, "💾 Aplicar",  self.ok,     style="Primary.TButton").pack(side="left", padx=4)
        btn(bf, "✖ Cancelar", self.cancel, style="Danger.TButton").pack(side="left",  padx=4)

    def ok(self) -> None:
        try:
            qty = int(self._qty_var.get() or 0)
        except ValueError:
            show_error(self, "La cantidad debe ser un número entero.")
            return
        if qty <= 0:
            show_error(self, "La cantidad debe ser mayor a 0.")
            return
        mv_type = self._type_var.get()
        note    = self._note_var.get().strip()
        self.result = (qty, mv_type, note)
        self.destroy()


# ============================================================
# INVENTORY VIEW
# ============================================================
class InventoryView(tk.Frame):
    """
    Vista de inventario con:
    - Resumen de stock actual
    - Alerta de stock bajo
    - Historial de movimientos
    - Ajuste manual de stock
    """

    def __init__(self, parent, auth: AuthService):
        super().__init__(parent, bg=THEME_BG)
        self._auth    = auth
        self._svc     = ProductService()
        self._can_adj = auth.current_user.role in (ROLE_ADMIN, ROLE_SUPERVISOR)
        self._build_ui()
        self._load()

    # ----------------------------------------------------------
    def _build_ui(self) -> None:
        hdr = tk.Frame(self, bg=THEME_PRIMARY, height=46)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📊  Control de Inventario",
                 bg=THEME_PRIMARY, fg="white",
                 font=(FONT_FAMILY, 14, "bold")).pack(side="left", padx=16, pady=10)

        # ── Tarjetas de resumen
        self._cards_frame = tk.Frame(self, bg=THEME_BG)
        self._cards_frame.pack(fill="x", padx=10, pady=8)

        self._card_total  = self._make_card("📦 Productos Activos", "—", THEME_PRIMARY)
        self._card_low    = self._make_card("⚠ Stock Bajo",          "—", THEME_WARNING)
        self._card_zero   = self._make_card("🚫 Sin Stock",           "—", THEME_DANGER)
        self._card_value  = self._make_card("💰 Valor en Inventario", "—", "#2980b9")

        # ── Toolbar
        tb = tk.Frame(self, bg=THEME_BG)
        tb.pack(fill="x", padx=10, pady=(0, 4))
        btn(tb, "🔄 Actualizar",    self._load,          style="Secondary.TButton").pack(side="left", padx=3)
        if self._can_adj:
            btn(tb, "🔧 Ajustar Stock", self._adjust_stock, style="Primary.TButton").pack(side="left", padx=3)

        # Filtro de stock bajo
        self._low_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tb, text="Solo stock bajo",
                        variable=self._low_only_var,
                        command=self._load).pack(side="left", padx=8)

        # ── Tabla principal de inventario
        inv_frame = ttk.LabelFrame(self, text=" Estado del Inventario ")
        inv_frame.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self._inv_table = DataTable(inv_frame, columns=[
            ("code",     "Código",      90,  "w"),
            ("name",     "Producto",   180,  "w"),
            ("category", "Categoría",  120,  "w"),
            ("stock",    "Stock Act.", 80,   "center"),
            ("min",      "Stock Mín.", 80,   "center"),
            ("status",   "Estado",     100,  "center"),
            ("unit",     "Unidad",     70,   "center"),
            ("pprice",   "P.Compra",   100,  "e"),
            ("sprice",   "P.Venta",    100,  "e"),
            ("value",    "Valor Stock", 110, "e"),
        ])
        self._inv_table.pack(fill="both", expand=True, padx=8, pady=8)
        self._inv_table.bind("<<TreeviewSelect>>", lambda _: self._on_select())

        # ── Panel inferior: historial de movimientos del producto seleccionado
        mov_frame = ttk.LabelFrame(self, text=" Historial de movimientos — producto seleccionado ")
        mov_frame.pack(fill="x", padx=10, pady=(0, 8))

        self._mov_table = DataTable(mov_frame, columns=[
            ("date",   "Fecha/Hora",  160, "w"),
            ("type",   "Tipo",         90, "center"),
            ("qty",    "Cantidad",     70, "center"),
            ("before", "Stock Antes",  90, "center"),
            ("after",  "Stock Después",90, "center"),
            ("user",   "Usuario",     150, "w"),
            ("notes",  "Notas",       200, "w"),
        ])
        self._mov_table.pack(fill="x", padx=8, pady=(4, 8))

    # ----------------------------------------------------------
    def _make_card(self, title: str, value: str, color: str) -> dict:
        card = tk.Frame(self._cards_frame, bg=color, relief="flat", bd=0)
        card.pack(side="left", fill="both", expand=True, padx=4, pady=4, ipady=8, ipadx=12)
        tk.Label(card, text=title, bg=color, fg="white",
                 font=(FONT_FAMILY, 9)).pack(anchor="w", padx=10, pady=(6, 0))
        val_lbl = tk.Label(card, text=value, bg=color, fg="white",
                           font=(FONT_FAMILY, 18, "bold"))
        val_lbl.pack(anchor="w", padx=10, pady=(0, 6))
        return {"frame": card, "label": val_lbl}

    def _update_card(self, card: dict, value: str) -> None:
        card["label"].config(text=value)

    # ----------------------------------------------------------
    def _load(self) -> None:
        low_only = self._low_only_var.get()
        prods = self._svc.low_stock() if low_only else self._svc.list_all()
        rows, tags = [], []
        total_value = 0.0
        low_count   = 0
        zero_count  = 0

        for p in prods:
            val = p.stock * p.sale_price
            total_value += val
            is_low  = p.stock < p.min_stock
            is_zero = p.stock == 0
            if is_low:  low_count += 1
            if is_zero: zero_count += 1

            status_txt = "🚫 SIN STOCK" if is_zero else ("⚠ BAJO" if is_low else "✅ OK")
            rows.append((
                p.code, p.name, p.category_name,
                p.stock, p.min_stock, status_txt, p.unit,
                f"$ {p.purchase_price:,.0f}",
                f"$ {p.sale_price:,.0f}",
                f"$ {val:,.0f}"
            ))
            tag = ("danger" if is_zero else ("low" if is_low else
                   ("even" if len(rows) % 2 == 0 else "odd")))
            tags.append(tag)

        self._inv_table.load(rows, tags)
        self._update_card(self._card_total, str(len(prods)))
        self._update_card(self._card_low,   str(low_count))
        self._update_card(self._card_zero,  str(zero_count))
        self._update_card(self._card_value, f"$ {total_value:,.0f}")

    def _on_select(self) -> None:
        row = self._inv_table.selected_row()
        if row is None:
            return
        code = row[0]
        prod = self._svc.find_by_code(code)
        if prod is None:
            return
        from repositories import InventoryMovementRepository
        repo = InventoryMovementRepository()
        movs = repo.find_by_product(prod.id)
        mov_rows = []
        for m in movs:
            dt = m["created_at"]
            dt_str = dt.strftime("%d/%m/%Y %H:%M") if dt else ""
            mov_rows.append((
                dt_str,
                m["movement_type"].upper(),
                m["quantity"],
                m["stock_before"],
                m["stock_after"],
                m.get("employee_name", ""),
                m.get("notes", "")
            ))
        self._mov_table.load(mov_rows)

    # ----------------------------------------------------------
    def _adjust_stock(self) -> None:
        row = self._inv_table.selected_row()
        if row is None:
            show_error(self, "Selecciona un producto primero.")
            return
        prod = self._svc.find_by_code(row[0])
        if prod is None:
            return
        d = StockAdjustDialog(self, prod)
        if d.result:
            qty, mv_type, note = d.result
            try:
                self._svc.adjust_stock(
                    product_id=prod.id,
                    delta=qty,
                    movement_type=mv_type,
                    employee_id=self._auth.current_user.id,
                    notes=note
                )
                show_info(self, f"Stock ajustado. Nuevo stock: {prod.stock + qty}")
                self._load()
            except (ValueError, RuntimeError) as e:
                show_error(self, str(e))
