# ============================================================
# ui/employees_view.py — Gestión de Empleados
# ============================================================

import tkinter as tk
from tkinter import ttk

from config import (THEME_PRIMARY, THEME_BG, THEME_WHITE,
                    THEME_TEXT, FONT_FAMILY, ALL_ROLES)
from services import AuthService, EmployeeService
from models import Employee
from ui.components import (DataTable, btn, FormDialog,
                            show_error, show_info, confirm)


# ============================================================
# EMPLOYEE FORM DIALOG
# ============================================================
class EmployeeFormDialog(FormDialog):

    def __init__(self, parent, employee: Employee = None):
        self._emp     = employee or Employee()
        self._is_edit = employee is not None
        super().__init__(parent,
                         title="Editar Empleado" if self._is_edit else "Nuevo Empleado",
                         width=500, height=600)

    def _build_ui(self) -> None:
        self.configure(bg=THEME_BG)
        ttk.Label(self, text="👤 Datos del Empleado",
                  font=(FONT_FAMILY, 13, "bold"),
                  foreground=THEME_PRIMARY, background=THEME_BG).pack(pady=(16, 8))

        form = tk.Frame(self, bg=THEME_BG)
        form.pack(fill="both", expand=True, padx=24)
        form.columnconfigure(1, weight=1)

        self._id_var    = self._field(form, "Identificación *",  0)
        self._fname_var = self._field(form, "Nombres *",          1)
        self._lname_var = self._field(form, "Apellidos *",        2)
        self._phone_var = self._field(form, "Celular",            3)
        self._email_var = self._field(form, "Correo",             4)
        self._role_var  = self._field(form, "Rol *", 5,
                                      widget_type="combo", values=ALL_ROLES)
        self._sal_var   = self._field(form, "Salario ($)",        6,
                                      widget_type="spinbox")

        # Contraseña (siempre requerida para nuevo, opcional para edición)
        pw_label = "Contraseña *" if not self._is_edit else "Nueva contraseña (vacío = sin cambio)"
        self._pw_var = self._field(form, pw_label, 7, widget_type="password")

        if self._is_edit:
            e = self._emp
            self._id_var.set(e.identification)
            self._fname_var.set(e.first_name)
            self._lname_var.set(e.last_name)
            self._phone_var.set(e.phone)
            self._email_var.set(e.email)
            self._role_var.set(e.role)
            self._sal_var.set(str(e.salary))

        bf = tk.Frame(self, bg=THEME_BG)
        bf.pack(fill="x", padx=24, pady=12)
        btn(bf, "💾 Guardar", self.ok,     style="Primary.TButton").pack(side="left", padx=4)
        btn(bf, "✖ Cancelar", self.cancel, style="Danger.TButton").pack(side="left", padx=4)

    def ok(self) -> None:
        e = self._emp
        e.identification = self._id_var.get().strip()
        e.first_name     = self._fname_var.get().strip()
        e.last_name      = self._lname_var.get().strip()
        e.phone          = self._phone_var.get().strip()
        e.email          = self._email_var.get().strip()
        e.role           = self._role_var.get()
        try:
            e.salary = float(self._sal_var.get() or 0)
        except ValueError:
            show_error(self, "Salario inválido.")
            return

        pw = self._pw_var.get().strip()
        if not self._is_edit and not pw:
            show_error(self, "La contraseña es obligatoria para nuevos empleados.")
            return
        if pw and len(pw) < 6:
            show_error(self, "La contraseña debe tener mínimo 6 caracteres.")
            return

        self.result = (e, pw)
        self.destroy()


# ============================================================
# EMPLOYEES VIEW
# ============================================================
class EmployeesView(tk.Frame):

    def __init__(self, parent, auth: AuthService):
        super().__init__(parent, bg=THEME_BG)
        self._auth = auth
        self._svc  = EmployeeService()
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        hdr = tk.Frame(self, bg=THEME_PRIMARY, height=46)
        hdr.pack(fill="x")
        tk.Label(hdr, text="👥  Gestión de Empleados",
                 bg=THEME_PRIMARY, fg="white",
                 font=(FONT_FAMILY, 14, "bold")).pack(side="left", padx=16, pady=10)

        tb = tk.Frame(self, bg=THEME_BG)
        tb.pack(fill="x", padx=10, pady=6)
        btn(tb, "➕ Nuevo",       self._new,        style="Primary.TButton").pack(side="left",  padx=3)
        btn(tb, "✏ Editar",       self._edit,       style="Secondary.TButton").pack(side="left", padx=3)
        btn(tb, "✅ Activar",     self._activate,   style="Success.TButton").pack(side="right", padx=3)
        btn(tb, "⛔ Desactivar",  self._deactivate, style="Danger.TButton").pack(side="right",  padx=3)
        btn(tb, "🗑 Eliminar",    self._delete,     style="Danger.TButton").pack(side="right",  padx=3)

        self._table = DataTable(self, columns=[
            ("id",    "ID",           60,  "center"),
            ("ident", "Identificación", 130, "w"),
            ("name",  "Nombre",       200, "w"),
            ("role",  "Rol",          120, "center"),
            ("phone", "Celular",      110, "center"),
            ("email", "Correo",       200, "w"),
            ("salary","Salario",      100, "e"),
            ("status","Estado",       90,  "center"),
        ])
        self._table.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self._table.bind("<Double-1>", lambda _: self._edit())

    def _load(self) -> None:
        emps = self._svc.list_all()
        self._items = emps
        rows, tags = [], []
        for e in emps:
            rows.append((
                e.id, e.identification, e.full_name, e.role,
                e.phone, e.email,
                f"$ {e.salary:,.0f}",
                "✅ Activo" if e.active else "❌ Inactivo"
            ))
            tag = "even" if len(rows) % 2 == 0 else "odd"
            if not e.active:
                tag = "danger"
            tags.append(tag)
        self._table.load(rows, tags)

    def _selected_emp(self) -> Employee | None:
        row = self._table.selected_row()
        if row is None:
            show_error(self, "Selecciona un empleado.")
            return None
        emp_id = int(row[0])
        return self._svc.find(emp_id)

    def _new(self) -> None:
        d = EmployeeFormDialog(self)
        if d.result:
            emp, pw = d.result
            try:
                self._svc.create(emp, pw)
                show_info(self, f"Empleado '{emp.full_name}' creado correctamente.")
                self._load()
            except ValueError as e:
                show_error(self, str(e))

    def _edit(self) -> None:
        emp = self._selected_emp()
        if emp is None:
            return
        # No permitir editar al admin actual
        d = EmployeeFormDialog(self, employee=emp)
        if d.result:
            emp_upd, pw = d.result
            try:
                self._svc.update(emp_upd)
                if pw:
                    self._svc.change_password(emp_upd.id, pw)
                show_info(self, "Empleado actualizado correctamente.")
                self._load()
            except ValueError as e:
                show_error(self, str(e))

    def _activate(self) -> None:
        emp = self._selected_emp()
        if emp is None:
            return
        self._svc.activate(emp.id)
        show_info(self, f"'{emp.full_name}' activado.")
        self._load()

    def _deactivate(self) -> None:
        emp = self._selected_emp()
        if emp is None:
            return
        if emp.id == self._auth.current_user.id:
            show_error(self, "No puedes desactivar tu propia cuenta.")
            return
        if confirm(self, "Desactivar", f"¿Desactivar a '{emp.full_name}'?"):
            self._svc.deactivate(emp.id)
            self._load()

    def _delete(self) -> None:
        emp = self._selected_emp()
        if emp is None:
            return
        if emp.id == self._auth.current_user.id:
            show_error(self, "No puedes eliminar tu propia cuenta.")
            return
        if confirm(self, "Eliminar",
                   f"¿Eliminar permanentemente a '{emp.full_name}'? Esta acción no se puede deshacer."):
            self._svc.delete(emp.id)
            show_info(self, "Empleado eliminado.")
            self._load()
