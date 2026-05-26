# ============================================================
# ui/app.py — Ventana principal de la aplicación
# ============================================================

import tkinter as tk
from tkinter import messagebox
import os

try:
    from PIL import Image, ImageTk
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

from config import THEME_BG, COMPANY_NAME, LOGO_PATH
from services import AuthService
from ui.components import ThemeManager


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self._auth = AuthService()
        self._configure_window()
        ThemeManager.apply(self)
        self._show_login()

    def _configure_window(self) -> None:
        self.title(f"{COMPANY_NAME} — Sistema POS")
        self.configure(bg=THEME_BG)
        self.minsize(1100, 680)
        self._center_window(1280, 760)
        self._set_icon()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self, w: int, h: int) -> None:
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _set_icon(self) -> None:
        if PILLOW_OK and os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH).resize((32, 32), Image.LANCZOS)
                self._icon = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icon)
            except Exception:
                pass

    def _show_login(self) -> None:
        from ui.login_view import LoginView
        LoginView(self, self._auth, on_success=self._on_login_success)

    def _on_login_success(self, user) -> None:
        from ui.dashboard_view import DashboardView
        DashboardView(self, self._auth, on_logout=self._on_logout)

    def _on_logout(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()
        self._show_login()

    def _on_close(self) -> None:
        if messagebox.askokcancel("Salir", "¿Deseas cerrar el sistema POS?"):
            self.destroy()

    def run(self) -> None:
        self.mainloop()
