# ============================================================
# ui/login_view.py — Pantalla de inicio de sesión
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import os

# Pillow es opcional — sin ella se muestra un ícono de texto
try:
    from PIL import Image, ImageTk, ImageDraw
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

from config import (THEME_PRIMARY, THEME_SECONDARY, THEME_BG, THEME_WHITE,
                    THEME_TEXT, FONT_FAMILY, LOGO_PATH, COMPANY_NAME)
from services import AuthService
from ui.components import show_error


class LoginView(tk.Frame):

    def __init__(self, parent: tk.Tk, auth: AuthService, on_success):
        super().__init__(parent, bg=THEME_PRIMARY)
        self._auth       = auth
        self._on_success = on_success
        self._id_var     = tk.StringVar()
        self._pw_var     = tk.StringVar()
        self._build_ui()
        self.pack(fill="both", expand=True)

    def _build_ui(self) -> None:
        card = tk.Frame(self, bg=THEME_WHITE, relief="flat")
        card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=560)

        self._load_logo(card)

        tk.Label(card, text=COMPANY_NAME, bg=THEME_WHITE, fg=THEME_PRIMARY,
                 font=(FONT_FAMILY, 18, "bold")).pack(pady=(4, 0))
        tk.Label(card, text="Sistema de Punto de Venta",
                 bg=THEME_WHITE, fg="#888",
                 font=(FONT_FAMILY, 10)).pack(pady=(0, 20))

        tk.Frame(card, bg=THEME_SECONDARY, height=3).pack(fill="x", padx=40)

        form = tk.Frame(card, bg=THEME_WHITE)
        form.pack(pady=20, padx=50, fill="x")

        self._make_field(form, "Identificación", self._id_var, show=None)
        self._make_field(form, "Contraseña",     self._pw_var, show="●")

        tk.Button(
            card, text="INICIAR SESIÓN", command=self._login,
            bg=THEME_PRIMARY, fg=THEME_WHITE,
            font=(FONT_FAMILY, 11, "bold"),
            relief="flat", cursor="hand2",
            activebackground="#155228", activeforeground=THEME_WHITE,
            padx=20, pady=10
        ).pack(pady=10, padx=50, fill="x")

        self.bind_all("<Return>", lambda _: self._login())

        tk.Label(card, text="© 2025 Supermercado DTo2  —  v1.0",
                 bg=THEME_WHITE, fg="#bbb",
                 font=(FONT_FAMILY, 8)).pack(side="bottom", pady=10)

    def _load_logo(self, parent) -> None:
        """Carga el logo con Pillow si está disponible; si no, muestra emoji."""
        if PILLOW_OK and os.path.exists(LOGO_PATH):
            try:
                img  = Image.open(LOGO_PATH).resize((110, 110), Image.LANCZOS)
                mask = Image.new("L", img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + img.size, fill=255)
                out  = Image.new("RGBA", img.size, (255, 255, 255, 0))
                out.paste(img, mask=mask)
                self._logo_img = ImageTk.PhotoImage(out)
                tk.Label(parent, image=self._logo_img,
                         bg=THEME_WHITE).pack(pady=(30, 8))
                return
            except Exception:
                pass
        # Fallback sin Pillow
        tk.Label(parent, text="🛒", font=(FONT_FAMILY, 52),
                 bg=THEME_WHITE, fg=THEME_PRIMARY).pack(pady=(30, 8))

    def _make_field(self, parent, label: str, var, show=None) -> None:
        tk.Label(parent, text=label, bg=THEME_WHITE, fg=THEME_TEXT,
                 font=(FONT_FAMILY, 10), anchor="w").pack(fill="x", pady=(8, 2))
        tk.Entry(parent, textvariable=var, show=show or "",
                 bg="#f0f4f0", fg=THEME_TEXT, font=(FONT_FAMILY, 11),
                 relief="flat",
                 insertbackground=THEME_PRIMARY).pack(fill="x", ipady=8)
        tk.Frame(parent, bg=THEME_PRIMARY, height=2).pack(fill="x")

    def _login(self) -> None:
        ident = self._id_var.get().strip()
        passw = self._pw_var.get().strip()
        if not ident:
            show_error(self, "Ingresa tu identificación.")
            return
        if not passw:
            show_error(self, "Ingresa tu contraseña.")
            return
        try:
            user = self._auth.login(ident, passw)
            self._pw_var.set("")
            self.pack_forget()
            self._on_success(user)
        except ValueError as e:
            show_error(self, str(e))
            self._pw_var.set("")
