# ============================================================
# ui/sales_view.py — Módulo de ventas con carrito
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config import (THEME_PRIMARY, THEME_SECONDARY, THEME_BG, THEME_WHITE,
                    THEME_DANGER, THEME_SUCCESS, THEME_TEXT, FONT_FAMILY,
                    THEME_WARNING)
from services import AuthService, ProductService, SaleService, CartService
from models import CartItem
from ui.components import (DataTable, btn, section_label, SearchBar,
                            show_error, show_info, confirm)


class SalesView(tk.Frame):
    """
    Módulo completo de ventas:
    - Búsqueda de productos
    - Carrito interactivo
    - Cobro y generación de factura
    """

    def __init__(self, parent, auth: AuthService):
        super().__init__(parent, bg=THEME_BG)
        self._auth    = auth
        self._prod_svc = ProductService()
        self._sale_svc = SaleService()
        self._cart     = CartService()
        self._build_ui()

    # ----------------------------------------------------------
    def _build_ui(self) -> None:
        # ── Título
        header = tk.Frame(self, bg=THEME_PRIMARY, height=46)
        header.pack(fill="x")
        tk.Label(header, text="🛒  Nueva Venta", bg=THEME_PRIMARY, fg=THEME_WHITE,
                 font=(FONT_FAMILY, 14, "bold")).pack(side="left", padx=16, pady=10)

        body = tk.Frame(self, bg=THEME_BG)
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # ── Panel izquierdo: búsqueda de productos
        left = ttk.LabelFrame(body, text=" Catálogo de Productos ")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=4)

        # Barra de búsqueda
        sb = SearchBar(left, "Buscar por nombre o código...",
                       on_search=self._search_products)
        sb.pack(fill="x", padx=8, pady=6)

        self._prod_table = DataTable(left, columns=[
            ("code",  "Código",   90,  "w"),
            ("name",  "Producto", 200, "w"),
            ("price", "Precio",   90,  "e"),
            ("stock", "Stock",    60,  "center"),
        ])
        self._prod_table.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._prod_table.bind("<Double-1>", lambda _: self._add_selected_to_cart())
        self._prod_table.bind("<Return>",   lambda _: self._add_selected_to_cart())

        qty_row = tk.Frame(left, bg=THEME_BG)
        qty_row.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(qty_row, text="Cantidad:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left")
        self._qty_var = tk.IntVar(value=1)
        ttk.Spinbox(qty_row, textvariable=self._qty_var, from_=1, to=9999,
                    width=6).pack(side="left", padx=6)
        btn(qty_row, "➕ Agregar", self._add_selected_to_cart,
            style="Primary.TButton").pack(side="left", padx=4)

        # ── Panel derecho: carrito
        right = ttk.LabelFrame(body, text=" Carrito de Compras ")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=4)

        self._cart_table = DataTable(right, columns=[
            ("prod",  "Producto",  200, "w"),
            ("qty",   "Cant.",     55,  "center"),
            ("price", "P. Unit.",  90,  "e"),
            ("total", "Subtotal",  100, "e"),
        ])
        self._cart_table.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        # Botones carrito
        cart_btns = tk.Frame(right, bg=THEME_BG)
        cart_btns.pack(fill="x", padx=8, pady=4)
        btn(cart_btns, "🗑 Quitar",  self._remove_cart_item, style="Danger.TButton").pack(side="left", padx=2)
        btn(cart_btns, "🧹 Vaciar",  self._clear_cart,       style="Danger.TButton").pack(side="left", padx=2)

        # ── Totales
        tot_frame = tk.Frame(right, bg=THEME_WHITE, relief="groove", bd=1)
        tot_frame.pack(fill="x", padx=8, pady=6)

        def tot_row(label, var, big=False):
            r = tk.Frame(tot_frame, bg=THEME_WHITE)
            r.pack(fill="x", padx=12, pady=2)
            sz = 13 if big else 10
            tk.Label(r, text=label, bg=THEME_WHITE, fg=THEME_TEXT,
                     font=(FONT_FAMILY, sz)).pack(side="left")
            tk.Label(r, textvariable=var, bg=THEME_WHITE,
                     fg=(THEME_PRIMARY if big else THEME_TEXT),
                     font=(FONT_FAMILY, sz, "bold")).pack(side="right")

        self._subtotal_var = tk.StringVar(value="$ 0")
        self._tax_var      = tk.StringVar(value="$ 0")
        self._total_var    = tk.StringVar(value="$ 0")
        self._change_var   = tk.StringVar(value="$ 0")

        tot_row("Subtotal:",  self._subtotal_var)
        tot_row("IVA (19%):", self._tax_var)
        tk.Frame(tot_frame, bg=THEME_PRIMARY, height=2).pack(fill="x", padx=8)
        tot_row("TOTAL:",     self._total_var,  big=True)

        # Pago
        pay_frame = tk.Frame(right, bg=THEME_BG)
        pay_frame.pack(fill="x", padx=8, pady=4)
        tk.Label(pay_frame, text="Pago recibido ($):", bg=THEME_BG,
                 font=(FONT_FAMILY, 10)).pack(side="left")
        self._paid_var = tk.StringVar(value="0")
        ttk.Entry(pay_frame, textvariable=self._paid_var, width=14,
                  font=(FONT_FAMILY, 12)).pack(side="left", padx=6)
        self._paid_var.trace_add("write", lambda *_: self._update_change())

        self._method_var = tk.StringVar(value="efectivo")
        ttk.Combobox(pay_frame, textvariable=self._method_var,
                     values=["efectivo", "tarjeta", "transferencia"],
                     state="readonly", width=13).pack(side="left", padx=4)

        tot_row("Cambio:",    self._change_var)

        # Botón cobrar
        btn(right, "💳  COBRAR VENTA", self._checkout,
            style="Success.TButton").pack(fill="x", padx=8, pady=6, ipady=6)

        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._load_products()

    # ----------------------------------------------------------
    def _load_products(self, term: str = "") -> None:
        prods = (self._prod_svc.search(term) if term
                 else self._prod_svc.list_all())
        rows = []
        tags = []
        for p in prods:
            rows.append((p.code, p.name,
                         f"$ {p.sale_price:,.0f}", p.stock))
            tags.append("low" if p.is_low_stock else
                        ("odd" if len(rows) % 2 == 0 else "even"))
        self._prod_table.load(rows, tags)
        self._products = prods   # cache

    def _search_products(self, term: str) -> None:
        self._load_products(term)

    # ----------------------------------------------------------
    def _add_selected_to_cart(self) -> None:
        row = self._prod_table.selected_row()
        if not row:
            show_error(self, "Selecciona un producto primero.")
            return
        code = row[0]
        prod = self._prod_svc.find_by_code(code)
        if prod is None:
            show_error(self, "Producto no encontrado.")
            return
        qty = self._qty_var.get()
        try:
            self._cart.add_item(prod, qty)
            self._refresh_cart()
        except ValueError as e:
            show_error(self, str(e))

    def _remove_cart_item(self) -> None:
        row = self._cart_table.selected_row()
        if not row:
            return
        # Buscar por nombre en el carrito
        name = row[0]
        for item in self._cart.items:
            if item.product.name == name:
                self._cart.remove_item(item.product.id)
                break
        self._refresh_cart()

    def _clear_cart(self) -> None:
        if confirm(self, "Vaciar carrito", "¿Deseas vaciar el carrito?"):
            self._cart.clear()
            self._refresh_cart()

    def _refresh_cart(self) -> None:
        rows = [(i.product.name, i.quantity,
                 f"$ {i.unit_price:,.0f}", f"$ {i.subtotal:,.0f}")
                for i in self._cart.items]
        self._cart_table.load(rows)
        self._subtotal_var.set(f"$ {self._cart.subtotal:,.0f}")
        self._tax_var.set(f"$ {self._cart.tax:,.0f}")
        self._total_var.set(f"$ {self._cart.total:,.0f}")
        self._update_change()

    def _update_change(self) -> None:
        try:
            paid = float(self._paid_var.get() or 0)
            change = self._cart.calculate_change(paid)
            self._change_var.set(f"$ {change:,.0f}")
        except ValueError:
            self._change_var.set("$ 0")

    # ----------------------------------------------------------
    def _checkout(self) -> None:
        if self._cart.is_empty():
            show_error(self, "El carrito está vacío.")
            return
        try:
            paid = float(self._paid_var.get() or 0)
        except ValueError:
            show_error(self, "Ingresa un monto de pago válido.")
            return
        if paid < self._cart.total:
            show_error(self, f"Pago insuficiente.\n"
                             f"Total: $ {self._cart.total:,.0f}\n"
                             f"Recibido: $ {paid:,.0f}")
            return
        method = self._method_var.get()
        try:
            sale = self._sale_svc.checkout(
                self._cart,
                employee_id=self._auth.current_user.id,
                paid_amount=paid,
                payment_method=method
            )
            self._cart.clear()
            self._refresh_cart()
            self._paid_var.set("0")
            self._load_products()

            # Mostrar resumen y ofrecer imprimir
            msg = (f"✅ Venta registrada exitosamente\n\n"
                   f"Factura: {sale.invoice_number}\n"
                   f"Total: $ {sale.total:,.0f}\n"
                   f"Pagado: $ {sale.paid_amount:,.0f}\n"
                   f"Cambio: $ {sale.change_amount:,.0f}")
            if messagebox.askyesno("Venta exitosa",
                                   msg + "\n\n¿Deseas imprimir la factura?",
                                   parent=self):
                self._print_invoice(sale)
        except (ValueError, RuntimeError) as e:
            show_error(self, str(e))

    def _print_invoice(self, sale) -> None:
        from tkinter.filedialog import asksaveasfilename
        from utils import InvoicePDFGenerator
        filepath = asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"Factura_{sale.invoice_number}.pdf",
            parent=self
        )
        if not filepath:
            return
        try:
            gen = InvoicePDFGenerator()
            # Aseguramos que el sale tenga employee_name
            sale.employee_name = self._auth.current_user.full_name
            gen.generate(sale, filepath)
            show_info(self, f"Factura guardada en:\n{filepath}")
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.run(["open", filepath])
            else:
                subprocess.run(["xdg-open", filepath])
        except Exception as e:
            show_error(self, f"No se pudo generar el PDF:\n{e}")

import os
