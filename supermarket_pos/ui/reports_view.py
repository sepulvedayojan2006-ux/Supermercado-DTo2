# ============================================================
# ui/reports_view.py — Módulo de Reportes
# ============================================================

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta, date
import threading

from config import (THEME_PRIMARY, THEME_SECONDARY, THEME_BG, THEME_WHITE,
                    THEME_TEXT, THEME_DANGER, THEME_SUCCESS, FONT_FAMILY)
from services import AuthService, ReportService
from ui.components import (DataTable, btn, show_error, show_info)


# ============================================================
# REPORTS VIEW
# ============================================================
class ReportsView(tk.Frame):
    """
    Reportes disponibles:
    1. Ventas diarias
    2. Ventas por rango de fechas
    3. Productos más vendidos
    4. Stock actual / bajo inventario
    5. Resumen mensual
    6. Ventas por empleado
    """

    def __init__(self, parent, auth: AuthService):
        super().__init__(parent, bg=THEME_BG)
        self._auth = auth
        self._svc  = ReportService()
        self._build_ui()

    # ----------------------------------------------------------
    def _build_ui(self) -> None:
        hdr = tk.Frame(self, bg=THEME_PRIMARY, height=46)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📈  Reportes y Estadísticas",
                 bg=THEME_PRIMARY, fg="white",
                 font=(FONT_FAMILY, 14, "bold")).pack(side="left", padx=16, pady=10)

        # Notebook interno de reportes
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_daily_tab()
        self._build_range_tab()
        self._build_top_products_tab()
        self._build_stock_tab()
        self._build_monthly_tab()
        self._build_employee_tab()

    # ════════════════════════════════════════════════════════
    # TAB 1: Ventas Diarias
    # ════════════════════════════════════════════════════════
    def _build_daily_tab(self) -> None:
        f = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(f, text="  📅 Ventas Diarias  ")

        ctrl = tk.Frame(f, bg=THEME_BG)
        ctrl.pack(fill="x", padx=10, pady=10)
        tk.Label(ctrl, text="Fecha:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left")
        self._daily_date = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(ctrl, textvariable=self._daily_date, width=14).pack(side="left", padx=6)
        tk.Label(ctrl, text="(AAAA-MM-DD)", bg=THEME_BG, fg="#888",
                 font=(FONT_FAMILY, 9)).pack(side="left")
        btn(ctrl, "🔍 Generar", lambda: self._run_daily(), style="Primary.TButton").pack(side="left", padx=8)
        btn(ctrl, "📥 Exportar Excel", lambda: self._export_daily(), style="Secondary.TButton").pack(side="left")

        # Tarjetas KPI
        self._daily_cards = tk.Frame(f, bg=THEME_BG)
        self._daily_cards.pack(fill="x", padx=10, pady=4)
        self._dk_sales   = self._kpi(self._daily_cards, "Total de Ventas", "—", THEME_PRIMARY)
        self._dk_revenue = self._kpi(self._daily_cards, "Ingresos del Día", "—", "#2980b9")
        self._dk_taxes   = self._kpi(self._daily_cards, "IVA Recaudado",    "—", "#8e44ad")

        # Tabla de ventas del día
        self._daily_table = DataTable(f, columns=[
            ("inv",    "Factura",    120, "w"),
            ("time",   "Hora",        70, "center"),
            ("cashier","Cajero",     160, "w"),
            ("items",  "Ítems",       55, "center"),
            ("total",  "Total",      110, "e"),
            ("method", "Método",     100, "center"),
            ("status", "Estado",      90, "center"),
        ])
        self._daily_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self._daily_data = []

    def _run_daily(self) -> None:
        d = self._daily_date.get().strip()
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            show_error(self, "Formato de fecha inválido. Usa AAAA-MM-DD"); return

        summary = self._svc.daily_summary(d)
        self._dk_sales.config(  text=str(summary.get("total_sales", 0)))
        self._dk_revenue.config(text=f"$ {float(summary.get('revenue', 0)):,.0f}")
        self._dk_taxes.config(  text=f"$ {float(summary.get('taxes', 0)):,.0f}")

        # Detalle de ventas del día
        from repositories import SaleRepository
        sales = SaleRepository().find_by_date_range(d, d)
        rows = []
        for s in sales:
            t = s.sold_at.strftime("%H:%M") if s.sold_at else ""
            rows.append((s.invoice_number, t, s.employee_name,
                         len(s.details), f"$ {s.total:,.0f}",
                         s.payment_method, s.status))
        self._daily_table.load(rows)
        self._daily_data = [
            {"Factura": r[0], "Hora": r[1], "Cajero": r[2],
             "Ítems": r[3], "Total": r[4], "Método": r[5], "Estado": r[6]}
            for r in rows
        ]

    def _export_daily(self) -> None:
        if not self._daily_data:
            show_error(self, "Genera el reporte primero."); return
        self._export_excel(self._daily_data, "ventas_diarias")

    # ════════════════════════════════════════════════════════
    # TAB 2: Rango de Fechas
    # ════════════════════════════════════════════════════════
    def _build_range_tab(self) -> None:
        f = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(f, text="  📆 Por Rango  ")

        ctrl = tk.Frame(f, bg=THEME_BG)
        ctrl.pack(fill="x", padx=10, pady=10)
        tk.Label(ctrl, text="Desde:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left")
        self._r_start = tk.StringVar(value=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(ctrl, textvariable=self._r_start, width=13).pack(side="left", padx=4)
        tk.Label(ctrl, text="Hasta:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left", padx=(8, 0))
        self._r_end = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(ctrl, textvariable=self._r_end, width=13).pack(side="left", padx=4)
        btn(ctrl, "🔍 Generar",       lambda: self._run_range(),  style="Primary.TButton").pack(side="left", padx=8)
        btn(ctrl, "📥 Excel",         lambda: self._export_range(), style="Secondary.TButton").pack(side="left")

        # KPIs de rango
        kf = tk.Frame(f, bg=THEME_BG)
        kf.pack(fill="x", padx=10, pady=4)
        self._rk_days    = self._kpi(kf, "Días con Ventas", "—", THEME_PRIMARY)
        self._rk_total   = self._kpi(kf, "Total Ingresos",  "—", "#2980b9")
        self._rk_avg     = self._kpi(kf, "Promedio Diario", "—", "#27ae60")

        self._range_table = DataTable(f, columns=[
            ("date",    "Fecha",         120, "w"),
            ("qty",     "# Ventas",       80, "center"),
            ("revenue", "Ingresos",       130, "e"),
        ])
        self._range_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self._range_data = []

    def _run_range(self) -> None:
        start, end = self._r_start.get().strip(), self._r_end.get().strip()
        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end,   "%Y-%m-%d")
        except ValueError:
            show_error(self, "Formato de fecha inválido. Usa AAAA-MM-DD"); return
        data = self._svc.sales_by_range(start, end)
        rows = [(d["sale_date"].strftime("%d/%m/%Y") if hasattr(d["sale_date"], "strftime")
                 else str(d["sale_date"]),
                 d["qty"], f"$ {float(d['revenue']):,.0f}")
                for d in data]
        self._range_table.load(rows)
        total = sum(float(d["revenue"]) for d in data)
        days  = len(data)
        avg   = total / days if days else 0
        self._rk_days.config( text=str(days))
        self._rk_total.config(text=f"$ {total:,.0f}")
        self._rk_avg.config(  text=f"$ {avg:,.0f}")
        self._range_data = [
            {"Fecha": r[0], "# Ventas": r[1], "Ingresos": r[2]} for r in rows
        ]

    def _export_range(self) -> None:
        if not self._range_data:
            show_error(self, "Genera el reporte primero."); return
        self._export_excel(self._range_data, "ventas_rango")

    # ════════════════════════════════════════════════════════
    # TAB 3: Productos más vendidos
    # ════════════════════════════════════════════════════════
    def _build_top_products_tab(self) -> None:
        f = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(f, text="  🏆 Top Productos  ")

        ctrl = tk.Frame(f, bg=THEME_BG)
        ctrl.pack(fill="x", padx=10, pady=10)
        tk.Label(ctrl, text="Desde:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left")
        self._tp_start = tk.StringVar(value=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(ctrl, textvariable=self._tp_start, width=13).pack(side="left", padx=4)
        tk.Label(ctrl, text="Hasta:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left", padx=(8,0))
        self._tp_end = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(ctrl, textvariable=self._tp_end, width=13).pack(side="left", padx=4)
        tk.Label(ctrl, text="Top:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left", padx=(8,0))
        self._tp_limit = tk.IntVar(value=10)
        ttk.Spinbox(ctrl, textvariable=self._tp_limit, from_=5, to=50, width=5).pack(side="left", padx=4)
        btn(ctrl, "🔍 Generar", lambda: self._run_top(), style="Primary.TButton").pack(side="left", padx=8)
        btn(ctrl, "📥 Excel",   lambda: self._export_top(), style="Secondary.TButton").pack(side="left")

        self._top_table = DataTable(f, columns=[
            ("rank",    "#",             40,  "center"),
            ("product", "Producto",     280,  "w"),
            ("qty",     "Und. Vendidas", 110, "center"),
            ("revenue", "Ingresos",      130, "e"),
        ])
        self._top_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self._top_data = []

    def _run_top(self) -> None:
        start = self._tp_start.get().strip()
        end   = self._tp_end.get().strip()
        limit = self._tp_limit.get()
        data  = self._svc.top_products(limit=limit, start=start, end=end)
        rows  = [(i+1, d["product_name"], d["total_qty"],
                  f"$ {float(d['total_revenue']):,.0f}")
                 for i, d in enumerate(data)]
        self._top_table.load(rows)
        self._top_data = [
            {"#": r[0], "Producto": r[1], "Und. Vendidas": r[2], "Ingresos": r[3]}
            for r in rows
        ]

    def _export_top(self) -> None:
        if not self._top_data:
            show_error(self, "Genera el reporte primero."); return
        self._export_excel(self._top_data, "top_productos")

    # ════════════════════════════════════════════════════════
    # TAB 4: Stock actual
    # ════════════════════════════════════════════════════════
    def _build_stock_tab(self) -> None:
        f = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(f, text="  📦 Stock Actual  ")

        ctrl = tk.Frame(f, bg=THEME_BG)
        ctrl.pack(fill="x", padx=10, pady=10)
        btn(ctrl, "🔍 Actualizar",    lambda: self._run_stock(), style="Primary.TButton").pack(side="left", padx=3)
        btn(ctrl, "📥 Exportar Excel", lambda: self._export_stock(), style="Secondary.TButton").pack(side="left", padx=3)

        # Filtro de solo bajo stock
        self._stock_low_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl, text="Solo bajo inventario",
                        variable=self._stock_low_var,
                        command=self._run_stock).pack(side="left", padx=10)

        self._stock_table = DataTable(f, columns=[
            ("code",     "Código",       90, "w"),
            ("name",     "Producto",    200, "w"),
            ("category", "Categoría",   120, "w"),
            ("stock",    "Stock",        70, "center"),
            ("min",      "Mín.",         60, "center"),
            ("status",   "Estado",       90, "center"),
            ("price",    "P. Venta",    100, "e"),
            ("value",    "Valor Total", 120, "e"),
        ])
        self._stock_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self._stock_data = []
        self._run_stock()

    def _run_stock(self) -> None:
        data = self._svc.stock_report()
        low_only = self._stock_low_var.get()
        if low_only:
            data = [d for d in data if d["stock_status"] == "BAJO"]
        rows, tags = [], []
        for d in data:
            is_zero = d["stock"] == 0
            is_low  = d["stock_status"] == "BAJO"
            status  = "🚫 SIN STOCK" if is_zero else ("⚠ BAJO" if is_low else "✅ OK")
            rows.append((
                d["code"], d["name"], d["category"],
                d["stock"], d["min_stock"], status,
                f"$ {float(d['sale_price']):,.0f}",
                f"$ {float(d['stock_value']):,.0f}"
            ))
            tags.append("danger" if is_zero else ("low" if is_low else
                        ("even" if len(rows) % 2 == 0 else "odd")))
        self._stock_table.load(rows, tags)
        self._stock_data = [
            {"Código": r[0], "Producto": r[1], "Categoría": r[2],
             "Stock": r[3], "Mínimo": r[4], "Estado": r[5],
             "P. Venta": r[6], "Valor Total": r[7]}
            for r in rows
        ]

    def _export_stock(self) -> None:
        if not self._stock_data:
            show_error(self, "Sin datos para exportar."); return
        self._export_excel(self._stock_data, "reporte_stock")

    # ════════════════════════════════════════════════════════
    # TAB 5: Resumen Mensual
    # ════════════════════════════════════════════════════════
    def _build_monthly_tab(self) -> None:
        f = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(f, text="  📊 Mensual  ")

        ctrl = tk.Frame(f, bg=THEME_BG)
        ctrl.pack(fill="x", padx=10, pady=10)
        tk.Label(ctrl, text="Año:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left")
        self._m_year = tk.IntVar(value=date.today().year)
        ttk.Spinbox(ctrl, textvariable=self._m_year, from_=2020, to=2099, width=7).pack(side="left", padx=4)
        tk.Label(ctrl, text="Mes:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left", padx=(8,0))
        self._m_month = tk.IntVar(value=date.today().month)
        ttk.Spinbox(ctrl, textvariable=self._m_month, from_=1, to=12, width=5).pack(side="left", padx=4)
        btn(ctrl, "🔍 Generar", lambda: self._run_monthly(), style="Primary.TButton").pack(side="left", padx=8)

        kf = tk.Frame(f, bg=THEME_BG)
        kf.pack(fill="x", padx=10, pady=8)
        self._mk_sales  = self._kpi(kf, "Total Ventas",         "—", THEME_PRIMARY)
        self._mk_rev    = self._kpi(kf, "Ingresos del Mes",     "—", "#2980b9")
        self._mk_ticket = self._kpi(kf, "Ticket Promedio",      "—", "#27ae60")

        # Pequeña tabla de resumen por semana (opcional)
        self._monthly_table = DataTable(f, columns=[
            ("metric", "Métrica", 200, "w"),
            ("value",  "Valor",   200, "e"),
        ])
        self._monthly_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    def _run_monthly(self) -> None:
        year  = self._m_year.get()
        month = self._m_month.get()
        data  = self._svc.monthly(year, month)
        ts    = int(data.get("total_sales", 0))
        rev   = float(data.get("revenue", 0))
        avg   = float(data.get("avg_ticket", 0))
        self._mk_sales.config( text=str(ts))
        self._mk_rev.config(   text=f"$ {rev:,.0f}")
        self._mk_ticket.config(text=f"$ {avg:,.0f}")
        rows = [
            ("Total de ventas",          str(ts)),
            ("Ingresos totales",         f"$ {rev:,.0f}"),
            ("Ticket promedio",          f"$ {avg:,.0f}"),
            ("Período analizado",        f"{month:02d}/{year}"),
        ]
        self._monthly_table.load(rows)

    # ════════════════════════════════════════════════════════
    # TAB 6: Ventas por Empleado
    # ════════════════════════════════════════════════════════
    def _build_employee_tab(self) -> None:
        f = tk.Frame(self._nb, bg=THEME_BG)
        self._nb.add(f, text="  👤 Por Empleado  ")

        ctrl = tk.Frame(f, bg=THEME_BG)
        ctrl.pack(fill="x", padx=10, pady=10)
        tk.Label(ctrl, text="Desde:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left")
        self._e_start = tk.StringVar(value=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(ctrl, textvariable=self._e_start, width=13).pack(side="left", padx=4)
        tk.Label(ctrl, text="Hasta:", bg=THEME_BG, font=(FONT_FAMILY, 10)).pack(side="left", padx=(8,0))
        self._e_end = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(ctrl, textvariable=self._e_end, width=13).pack(side="left", padx=4)
        btn(ctrl, "🔍 Generar", lambda: self._run_employee(), style="Primary.TButton").pack(side="left", padx=8)
        btn(ctrl, "📥 Excel",   lambda: self._export_emp(),   style="Secondary.TButton").pack(side="left")

        self._emp_table = DataTable(f, columns=[
            ("employee", "Empleado",       200, "w"),
            ("sales",    "# Ventas",        90, "center"),
            ("revenue",  "Ingresos",        130, "e"),
        ])
        self._emp_table.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self._emp_data = []

    def _run_employee(self) -> None:
        start = self._e_start.get().strip()
        end   = self._e_end.get().strip()
        data  = self._svc.by_employee(start, end)
        rows  = [(d["employee"], d["total_sales"], f"$ {float(d['revenue']):,.0f}")
                 for d in data]
        self._emp_table.load(rows)
        self._emp_data = [
            {"Empleado": r[0], "# Ventas": r[1], "Ingresos": r[2]} for r in rows
        ]

    def _export_emp(self) -> None:
        if not self._emp_data:
            show_error(self, "Genera el reporte primero."); return
        self._export_excel(self._emp_data, "ventas_empleados")

    # ════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════
    def _kpi(self, parent, title: str, value: str, color: str) -> tk.Label:
        card = tk.Frame(parent, bg=color, relief="flat")
        card.pack(side="left", fill="both", expand=True, padx=4, pady=4, ipady=6, ipadx=10)
        tk.Label(card, text=title, bg=color, fg="white",
                 font=(FONT_FAMILY, 9)).pack(anchor="w", padx=8, pady=(4, 0))
        val_lbl = tk.Label(card, text=value, bg=color, fg="white",
                           font=(FONT_FAMILY, 16, "bold"))
        val_lbl.pack(anchor="w", padx=8, pady=(0, 4))
        return val_lbl

    def _export_excel(self, data: list[dict], name: str) -> None:
        from tkinter.filedialog import asksaveasfilename
        from utils import ExcelExporter
        fp = asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"{name}_{date.today()}.xlsx",
            parent=self
        )
        if not fp:
            return
        try:
            ExcelExporter.export(data, fp, name)
            show_info(self, f"Exportado exitosamente:\n{fp}")
        except Exception as e:
            show_error(self, f"Error al exportar:\n{e}")
