# ============================================================
# ui/dashboard_view.py — Panel principal con navegación
# ============================================================

import tkinter as tk
from tkinter import ttk
import os

try:
    from PIL import Image, ImageTk
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

from config import (THEME_PRIMARY, THEME_SECONDARY, THEME_BG, THEME_WHITE,
                    THEME_TEXT, FONT_FAMILY, LOGO_PATH, COMPANY_NAME, ROLE_ADMIN)
from services import AuthService
from ui.components import ThemeManager, StatusBar


class DashboardView(tk.Frame):

    def __init__(self, parent: tk.Tk, auth: AuthService, on_logout):
        super().__init__(parent, bg=THEME_BG)
        self._auth   = auth
        self._user   = auth.current_user
        self._logout = on_logout
        ThemeManager.apply(parent)
        self._build_ui()
        self.pack(fill="both", expand=True)

    def _build_ui(self) -> None:
        self._build_topbar()
        self._build_notebook()
        self._build_statusbar()

    def _build_topbar(self) -> None:
        bar = tk.Frame(self, bg=THEME_PRIMARY, height=56)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        self._load_topbar_logo(bar)

        tk.Label(bar, text=COMPANY_NAME, fg=THEME_WHITE, bg=THEME_PRIMARY,
                 font=(FONT_FAMILY, 14, "bold")).pack(side="left")

        tk.Label(bar,
                 text=f"👤 {self._user.full_name}  [{self._user.role}]",
                 fg="#c8e6c9", bg=THEME_PRIMARY,
                 font=(FONT_FAMILY, 10)).pack(side="right", padx=(0, 10))

        tk.Button(bar, text="⎋ Cerrar sesión",
                  bg=THEME_SECONDARY, fg=THEME_TEXT,
                  font=(FONT_FAMILY, 9, "bold"), relief="flat", cursor="hand2",
                  activebackground="#e09318",
                  command=self._do_logout,
                  padx=10, pady=5).pack(side="right", padx=8, pady=8)

    def _load_topbar_logo(self, parent) -> None:
        if PILLOW_OK and os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH).resize((40, 40), Image.LANCZOS)
                self._logo = ImageTk.PhotoImage(img)
                tk.Label(parent, image=self._logo,
                         bg=THEME_PRIMARY).pack(side="left", padx=(10, 6), pady=8)
                return
            except Exception:
                pass
        tk.Label(parent, text="🛒", fg=THEME_WHITE, bg=THEME_PRIMARY,
                 font=(FONT_FAMILY, 18)).pack(side="left", padx=10)

    def _build_notebook(self) -> None:
        from ui.sales_view     import SalesView
        from ui.products_view  import ProductsView
        from ui.employees_view import EmployeesView
        from ui.suppliers_view import SuppliersView
        from ui.reports_view   import ReportsView
        from ui.inventory_view import InventoryView

        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=8, pady=8)

        sf = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(sf, text="  🛒 Ventas  ")
        SalesView(sf, self._auth).pack(fill="both", expand=True)

        pf = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(pf, text="  📦 Productos  ")
        ProductsView(pf, self._auth).pack(fill="both", expand=True)

        invf = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(invf, text="  📊 Inventario  ")
        InventoryView(invf, self._auth).pack(fill="both", expand=True)

        supf = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(supf, text="  🚚 Proveedores  ")
        SuppliersView(supf, self._auth).pack(fill="both", expand=True)

        if self._user.role == ROLE_ADMIN:
            emf = tk.Frame(self._nb, bg=THEME_BG)
            self._nb.add(emf, text="  👥 Empleados  ")
            EmployeesView(emf, self._auth).pack(fill="both", expand=True)

        ref = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(ref, text="  📈 Reportes  ")
        ReportsView(ref, self._auth).pack(fill="both", expand=True)

    def _build_statusbar(self) -> None:
        self._status = StatusBar(self)
        self._status.pack(fill="x", side="bottom")
        self._status.set(
            f"Sesión: {self._user.full_name}  |  Rol: {self._user.role}"
        )

    def _do_logout(self) -> None:
        from ui.components import confirm
        if confirm(self, "Cerrar sesión", "¿Seguro que deseas cerrar sesión?"):
            self._auth.logout()
            self.pack_forget()
            self.destroy()
            self._logout()
