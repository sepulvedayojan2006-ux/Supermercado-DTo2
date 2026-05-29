# ============================================================
# ui/components/__init__.py — Componentes reutilizables de UI
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from config import (
    THEME_PRIMARY, THEME_SECONDARY, THEME_BG, THEME_WHITE,
    THEME_DANGER, THEME_SUCCESS, THEME_WARNING, THEME_TEXT,
    THEME_LIGHT, FONT_FAMILY
)


# ============================================================
# THEME MANAGER
# ============================================================
class ThemeManager:
    """Aplica el tema corporativo a todos los widgets ttk."""

    @staticmethod
    def apply(root: tk.Tk) -> None:
        style = ttk.Style(root)
        style.theme_use("clam")

        # Frame y fondo
        style.configure(".", background=THEME_BG, foreground=THEME_TEXT,
                         font=(FONT_FAMILY, 10))

        # TNotebook
        style.configure("TNotebook", background=THEME_BG, tabposition="n")
        style.configure("TNotebook.Tab",
                         background=THEME_LIGHT, foreground=THEME_TEXT,
                         padding=[14, 6], font=(FONT_FAMILY, 10))
        style.map("TNotebook.Tab",
                  background=[("selected", THEME_PRIMARY)],
                  foreground=[("selected", THEME_WHITE)])

        # Treeview
        style.configure("Treeview",
                         background=THEME_WHITE, foreground=THEME_TEXT,
                         rowheight=28, fieldbackground=THEME_WHITE,
                         font=(FONT_FAMILY, 10))
        style.configure("Treeview.Heading",
                         background=THEME_PRIMARY, foreground=THEME_WHITE,
                         font=(FONT_FAMILY, 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", THEME_SECONDARY)],
                  foreground=[("selected", THEME_TEXT)])

        # Buttons
        style.configure("Primary.TButton",
                         background=THEME_PRIMARY, foreground=THEME_WHITE,
                         font=(FONT_FAMILY, 10, "bold"),
                         padding=[12, 6], relief="flat")
        style.map("Primary.TButton",
                  background=[("active", "#155228"), ("pressed", "#0d3a1b")])

        style.configure("Secondary.TButton",
                         background=THEME_SECONDARY, foreground=THEME_TEXT,
                         font=(FONT_FAMILY, 10, "bold"),
                         padding=[12, 6], relief="flat")

        style.configure("Danger.TButton",
                         background=THEME_DANGER, foreground=THEME_WHITE,
                         font=(FONT_FAMILY, 10, "bold"),
                         padding=[12, 6], relief="flat")
        style.map("Danger.TButton",
                  background=[("active", "#c0392b")])

        style.configure("Success.TButton",
                         background=THEME_SUCCESS, foreground=THEME_WHITE,
                         font=(FONT_FAMILY, 10, "bold"),
                         padding=[12, 6], relief="flat")

        # Entry
        style.configure("TEntry", padding=[6, 4],
                         fieldbackground=THEME_WHITE, foreground=THEME_TEXT)

        # Combobox
        style.configure("TCombobox", padding=[6, 4],
                         fieldbackground=THEME_WHITE)

        # LabelFrame
        style.configure("TLabelframe", background=THEME_BG,
                         bordercolor=THEME_PRIMARY, relief="groove")
        style.configure("TLabelframe.Label",
                         background=THEME_BG, foreground=THEME_PRIMARY,
                         font=(FONT_FAMILY, 10, "bold"))


# ============================================================
# THEMED BUTTON HELPER
# ============================================================
def btn(parent, text, command, style="Primary.TButton", **kw):
    return ttk.Button(parent, text=text, command=command, style=style, **kw)


# ============================================================
# SECTION LABEL
# ============================================================
def section_label(parent, text: str) -> ttk.Label:
    lbl = ttk.Label(parent, text=text,
                    font=(FONT_FAMILY, 13, "bold"),
                    foreground=THEME_PRIMARY, background=THEME_BG)
    return lbl


# ============================================================
# STATUS BAR
# ============================================================
class StatusBar(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=THEME_PRIMARY, **kw)
        self._var = tk.StringVar(value="Listo")
        ttk.Label(self, textvariable=self._var,
                  background=THEME_PRIMARY, foreground=THEME_WHITE,
                  font=(FONT_FAMILY, 9), padding=[8, 3]).pack(side="left")

    def set(self, msg: str) -> None:
        self._var.set(msg)


# ============================================================
# DATA TABLE (Treeview con scroll y búsqueda)
# ============================================================
class DataTable(tk.Frame):
    """
    Tabla reutilizable basada en ttk.Treeview.
    Soporta scroll, selección, y color de filas alternas.
    """

    def __init__(self, parent, columns: list[tuple], **kw):
        """
        columns: lista de (id, heading, width, anchor)
        """
        super().__init__(parent, bg=THEME_BG, **kw)
        self._columns = columns
        self._build()

    def _build(self) -> None:
        col_ids = [c[0] for c in self._columns]
        self._tree = ttk.Treeview(self, columns=col_ids, show="headings",
                                   selectmode="browse")
        vsb = ttk.Scrollbar(self, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        for cid, heading, width, anchor in self._columns:
            self._tree.heading(cid, text=heading,
                               command=lambda c=cid: self._sort(c, False))
            self._tree.column(cid, width=width, anchor=anchor, minwidth=60)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Colores alternos
        self._tree.tag_configure("odd",  background=THEME_WHITE)
        self._tree.tag_configure("even", background="#f0f7f2")
        self._tree.tag_configure("low",  background="#fff3cd")   # stock bajo
        self._tree.tag_configure("danger", background="#fde8e8")  # inactivo/peligro

    def load(self, rows: list[tuple], tags: list[str] = None) -> None:
        """Carga una lista de tuplas. tags puede sobreescribir el tag de cada fila."""
        self._tree.delete(*self._tree.get_children())
        for i, row in enumerate(rows):
            tag = (tags[i] if tags and i < len(tags) else
                   ("odd" if i % 2 == 0 else "even"))
            self._tree.insert("", "end", iid=str(i), values=row, tags=(tag,))

    def selected_row(self) -> tuple | None:
        sel = self._tree.selection()
        if not sel:
            return None
        return self._tree.item(sel[0])["values"]

    def selected_iid(self) -> str | None:
        sel = self._tree.selection()
        return sel[0] if sel else None

    def bind(self, event, callback):
        self._tree.bind(event, callback)

    def _sort(self, col: str, reverse: bool) -> None:
        data = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        try:
            data.sort(key=lambda x: float(x[0].replace("$","").replace(",","").strip()),
                      reverse=reverse)
        except ValueError:
            data.sort(key=lambda x: x[0].lower(), reverse=reverse)
        for idx, (_, k) in enumerate(data):
            self._tree.move(k, "", idx)
        self._tree.heading(col, command=lambda: self._sort(col, not reverse))


# ============================================================
# FORM DIALOG BASE
# ============================================================
class FormDialog(tk.Toplevel):
    """Diálogo modal reutilizable para formularios."""

    def __init__(self, parent, title: str, width: int = 500, height: int = 500):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.resizable(False, False)
        self.configure(bg=THEME_BG)
        self.geometry(f"{width}x{height}")
        self.transient(parent)
        self.grab_set()
        self._center(parent)
        self._build_ui()
        self.wait_window()

    def _center(self, parent) -> None:
        parent.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"+{px - self.winfo_reqwidth()//2}+{py - self.winfo_reqheight()//2}")

    def _build_ui(self) -> None:
        """Override en subclases."""

    def _field(self, parent, label: str, row: int,
               var=None, widget_type="entry", values=None) -> tk.Variable:
        ttk.Label(parent, text=label, font=(FONT_FAMILY, 10)).grid(
            row=row, column=0, sticky="w", padx=8, pady=4)
        if var is None:
            var = tk.StringVar()
        if widget_type == "entry":
            w = ttk.Entry(parent, textvariable=var, width=32)
        elif widget_type == "combo":
            w = ttk.Combobox(parent, textvariable=var, values=values or [],
                             state="readonly", width=30)
        elif widget_type == "password":
            w = ttk.Entry(parent, textvariable=var, show="*", width=32)
        elif widget_type == "spinbox":
            w = ttk.Spinbox(parent, textvariable=var, from_=0, to=9999999,
                            width=30, increment=1)
        else:
            w = ttk.Entry(parent, textvariable=var, width=32)
        w.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        return var

    def ok(self) -> None:
        """Override para validar y cerrar."""
        self.destroy()

    def cancel(self) -> None:
        self.result = None
        self.destroy()


# ============================================================
# CONFIRM DIALOG
# ============================================================
def confirm(parent, title: str, message: str) -> bool:
    return messagebox.askyesno(title, message, parent=parent)


def show_error(parent, message: str) -> None:
    messagebox.showerror("Error", message, parent=parent)


def show_info(parent, message: str) -> None:
    messagebox.showinfo("Información", message, parent=parent)


def show_warning(parent, message: str) -> None:
    messagebox.showwarning("Advertencia", message, parent=parent)


# ============================================================
# SEARCH BAR
# ============================================================
class SearchBar(tk.Frame):
    def __init__(self, parent, placeholder: str, on_search, **kw):
        super().__init__(parent, bg=THEME_BG, **kw)
        self._placeholder = placeholder
        self._var = tk.StringVar()
        self._var.trace_add("write", lambda *_: self._on_change(on_search))
        ttk.Label(self, text="🔍", font=(FONT_FAMILY, 12),
                  background=THEME_BG).pack(side="left", padx=(0, 4))
        entry = ttk.Entry(self, textvariable=self._var, width=35,
                          font=(FONT_FAMILY, 11))
        entry.pack(side="left", fill="x", expand=True)
        entry.insert(0, placeholder)
        entry.bind("<FocusIn>",  lambda e: (entry.delete(0, "end")
                                            if entry.get() == placeholder else None))
        entry.bind("<FocusOut>", lambda e: (entry.insert(0, placeholder)
                                            if not entry.get() else None))

    def _on_change(self, on_search) -> None:
        text = self._var.get()
        # Si el texto es el placeholder o está vacío, buscar todo
        if text == self._placeholder or text == "":
            on_search("")
        else:
            on_search(text)

    def get(self) -> str:
        return self._var.get()

    def clear(self) -> None:
        self._var.set("")
