"""
views/main_view.py
Vista principal de CyberShield con ttkbootstrap
Tema: ciberseguridad — dark, verde neón / cian sobre negro
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText

THEME = "darkly"
FONT_TITLE  = ("Consolas", 20, "bold")
FONT_HEADER = ("Consolas", 12, "bold")
FONT_MONO   = ("Consolas", 10)
FONT_SMALL  = ("Consolas", 9)
FONT_STAT   = ("Consolas", 22, "bold")


class MainView(ttk.Window):
    """
    Ventana principal. Hereda de ttk.Window para integración total
    con ttkbootstrap. No contiene lógica de negocio.
    """

    def __init__(self, controller):
        super().__init__(
            title="⚡ CyberShield — Monitoreo de Incidentes de Ciberseguridad",
            themename=THEME,
            size=(1320, 820),
            minsize=(1050, 660),
        )
        self._ctrl = controller
        self._freq_data_cache: dict = {}
        self._sort_col = "Frecuencia"
        self._sort_asc = False

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    # ══════════════════════════════════════════
    #  CONSTRUCCIÓN DE UI
    # ══════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        content = ttk.Frame(self)
        content.pack(fill=BOTH, expand=True)
        self._build_sidebar(content)
        self._build_main_panel(content)
        self._build_statusbar()

    def _build_header(self):
        hdr = ttk.Frame(self, bootstyle="dark", padding=(18, 10))
        hdr.pack(fill=X)

        left = ttk.Frame(hdr, bootstyle="dark")
        left.pack(side=LEFT)
        ttk.Label(left, text="⚡ CYBER", font=("Consolas", 22, "bold"),
                  bootstyle="success").pack(side=LEFT)
        ttk.Label(left, text="SHIELD", font=("Consolas", 22, "bold"),
                  bootstyle="light").pack(side=LEFT)
        ttk.Label(left,
                  text="   ▸  Sistema Concurrente de Monitoreo de Incidentes  v1.0",
                  font=FONT_SMALL, bootstyle="secondary").pack(side=LEFT, padx=8)

        ttk.Button(hdr, text="⏻  SALIR Y GUARDAR",
                   bootstyle="danger-outline",
                   command=self._on_close, width=22).pack(side=RIGHT)
        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X)

    def _build_sidebar(self, parent):
        sb = ttk.Frame(parent, bootstyle="dark", padding=12, width=270)
        sb.pack(side=LEFT, fill=Y)
        sb.pack_propagate(False)

        # ── Stats ──────────────────────────────
        ttk.Label(sb, text="[ ESTADO DEL SISTEMA ]",
                  font=FONT_HEADER, bootstyle="success").pack(anchor=W, pady=(4, 8))

        self._stat_total    = self._stat_card(sb, "EVENTOS TOTALES",   "0", "success")
        self._stat_unique   = self._stat_card(sb, "CÓDIGOS ÚNICOS",    "0", "info")
        self._stat_critical = self._stat_card(sb, "ALERTAS CRÍTICAS",  "0", "danger")
        self._stat_excl     = self._stat_card(sb, "EXCLUSIONES",       "0", "warning")

        ttk.Separator(sb, orient=HORIZONTAL).pack(fill=X, pady=10)

        # ── Acciones principales ───────────────
        ttk.Label(sb, text="[ PROCESAMIENTO ]",
                  font=FONT_HEADER, bootstyle="success").pack(anchor=W, pady=(0, 8))

        self._btn_load = ttk.Button(
            sb, text="📂  Cargar Archivos .log",
            bootstyle="success", width=30,
            command=self._ctrl.action_select_and_process_files)
        self._btn_load.pack(fill=X, pady=3)

        self._btn_sample = ttk.Button(
            sb, text="🧪  Generar Logs de Muestra",
            bootstyle="info", width=30,
            command=self._ctrl.action_generate_and_process_samples)
        self._btn_sample.pack(fill=X, pady=3)

        ttk.Separator(sb, orient=HORIZONTAL).pack(fill=X, pady=10)

        # ── Consultas ──────────────────────────
        ttk.Label(sb, text="[ CONSULTAS ]",
                  font=FONT_HEADER, bootstyle="success").pack(anchor=W, pady=(0, 8))

        for text, style, cmd in [
            ("🔍  Consultar Frecuencia",   "info-outline",    self._open_query),
            ("🏆  Top 5 Incidentes",        "warning-outline", self._open_top5),
            ("📋  Reporte de Auditoría",    "success-outline", self._generate_audit),
            ("🚫  Gestionar Exclusiones",   "danger-outline",  self._open_exclusions),
        ]:
            ttk.Button(sb, text=text, bootstyle=style, width=30,
                       command=cmd).pack(fill=X, pady=2)

        ttk.Separator(sb, orient=HORIZONTAL).pack(fill=X, pady=10)

        for text, style, cmd in [
            ("💾  Guardar Estado",  "secondary-outline", self._save_state),
            ("🗑️  Limpiar Datos",   "secondary-outline", self._reset_data),
        ]:
            ttk.Button(sb, text=text, bootstyle=style, width=30,
                       command=cmd).pack(fill=X, pady=2)

    def _stat_card(self, parent, label, value, style):
        card = ttk.Frame(parent, bootstyle="dark", padding=5)
        card.pack(fill=X, pady=2)
        ttk.Label(card, text=label, font=FONT_SMALL,
                  bootstyle="secondary").pack(anchor=W)
        lbl = ttk.Label(card, text=value, font=FONT_STAT, bootstyle=style)
        lbl.pack(anchor=W)
        return lbl

    def _build_main_panel(self, parent):
        main = ttk.Frame(parent, padding=8)
        main.pack(side=LEFT, fill=BOTH, expand=True)

        nb = ttk.Notebook(main, bootstyle="dark")
        nb.pack(fill=BOTH, expand=True)

        t1 = ttk.Frame(nb); nb.add(t1, text="  📊 FRECUENCIAS  ")
        t2 = ttk.Frame(nb); nb.add(t2, text="  🚨 ALERTAS CRÍTICAS  ")
        t3 = ttk.Frame(nb); nb.add(t3, text="  🖥️ CONSOLA  ")

        self._build_freq_tab(t1)
        self._build_alerts_tab(t2)
        self._build_console_tab(t3)

    # ── Pestaña Frecuencias ────────────────────

    def _build_freq_tab(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill=X, pady=(0, 5))
        ttk.Label(bar, text="Mapa Global de Frecuencias de Eventos",
                  font=FONT_HEADER, bootstyle="success").pack(side=LEFT)
        ttk.Button(bar, text="↻ Actualizar", bootstyle="success-outline",
                   width=14, command=lambda: self.refresh_stats(None)).pack(side=RIGHT)

        sf = ttk.Frame(parent)
        sf.pack(fill=X, pady=(0, 5))
        ttk.Label(sf, text="🔎 Filtrar código: ", font=FONT_MONO).pack(side=LEFT)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._filter_freq_table)
        ttk.Entry(sf, textvariable=self._search_var, font=FONT_MONO,
                  width=32, bootstyle="info").pack(side=LEFT, padx=5)

        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=True)

        cols = ("Código", "Frecuencia", "Estado")
        self._freq_tree = ttk.Treeview(frame, columns=cols, show="headings",
                                        bootstyle="dark", height=22)
        for col in cols:
            self._freq_tree.heading(col, text=col,
                                    command=lambda c=col: self._sort_tree(c))
        self._freq_tree.column("Código",     width=280)
        self._freq_tree.column("Frecuencia", width=130, anchor=CENTER)
        self._freq_tree.column("Estado",     width=140, anchor=CENTER)
        self._freq_tree.tag_configure("critical", foreground="#ff4444")
        self._freq_tree.tag_configure("normal",   foreground="#66ff66")

        vsb = ttk.Scrollbar(frame, orient=VERTICAL,
                            command=self._freq_tree.yview, bootstyle="success-round")
        self._freq_tree.configure(yscrollcommand=vsb.set)
        self._freq_tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

    # ── Pestaña Alertas ────────────────────────

    def _build_alerts_tab(self, parent):
        ttk.Label(parent,
                  text="⚠  Incidentes que superaron el umbral crítico (≥ 50 apariciones)",
                  font=FONT_HEADER, bootstyle="danger").pack(anchor=W, pady=(0, 8))

        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=True)

        cols = ("Código", "Frecuencia", "Nivel de Riesgo")
        self._alert_tree = ttk.Treeview(frame, columns=cols, show="headings",
                                         bootstyle="danger", height=22)
        for col in cols:
            self._alert_tree.heading(col, text=col)
        self._alert_tree.column("Código",         width=280)
        self._alert_tree.column("Frecuencia",      width=130, anchor=CENTER)
        self._alert_tree.column("Nivel de Riesgo", width=180, anchor=CENTER)
        self._alert_tree.tag_configure("critical", foreground="#ff6666")
        self._alert_tree.tag_configure("extreme",  foreground="#ff0000",
                                       font=("Consolas", 10, "bold"))

        vsb2 = ttk.Scrollbar(frame, orient=VERTICAL,
                             command=self._alert_tree.yview, bootstyle="danger-round")
        self._alert_tree.configure(yscrollcommand=vsb2.set)
        self._alert_tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb2.pack(side=RIGHT, fill=Y)

    # ── Pestaña Consola ────────────────────────

    def _build_console_tab(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill=X, pady=(0, 5))
        ttk.Label(bar, text="Consola de Actividad del Sistema",
                  font=FONT_HEADER, bootstyle="success").pack(side=LEFT)
        ttk.Button(bar, text="🗑 Limpiar", bootstyle="secondary-outline",
                   width=12, command=self._clear_console).pack(side=RIGHT)

        self._console = ScrolledText(parent, height=28, autohide=True,
                                     bootstyle="success-round")
        self._console.pack(fill=BOTH, expand=True)
        self._console.text.configure(
            font=FONT_MONO, bg="#050d05", fg="#00ff41",
            insertbackground="#00ff41", state="disabled"
        )
        self.append_log("[ CyberShield v1.0 — Sistema inicializado ]")
        self.append_log("[ Use 'Generar Logs de Muestra' para probar rápidamente ]")

    # ── Statusbar ──────────────────────────────

    def _build_statusbar(self):
        bar = ttk.Frame(self, bootstyle="dark", padding=(12, 5))
        bar.pack(fill=X, side=BOTTOM)

        self._status_lbl = ttk.Label(bar, text="✅  Sistema listo",
                                      font=FONT_SMALL, bootstyle="success")
        self._status_lbl.pack(side=LEFT)

        self._prog_lbl = ttk.Label(bar, text="", font=FONT_SMALL,
                                   bootstyle="secondary")
        self._prog_lbl.pack(side=RIGHT, padx=6)

        self._prog_var = tk.DoubleVar(value=0)
        self._prog_bar = ttk.Progressbar(bar, variable=self._prog_var,
                                          bootstyle="success-striped", length=320)
        self._prog_bar.pack(side=RIGHT, padx=8)

    # ══════════════════════════════════════════
    #  ACTUALIZACIÓN DE DATOS
    # ══════════════════════════════════════════

    def refresh_stats(self, monitor):
        if monitor is None:
            freqs    = self._ctrl.action_get_all_frequencies()
            critical = self._ctrl.action_get_critical_codes()
            excl     = self._ctrl.action_get_exclusions()
        else:
            freqs    = monitor.get_all_frequencies()
            critical = monitor.get_critical_codes()
            excl     = monitor.get_exclusions()

        self._stat_total.configure(   text=f"{sum(freqs.values()):,}")
        self._stat_unique.configure(  text=str(len(freqs)))
        self._stat_critical.configure(text=str(len(critical)))
        self._stat_excl.configure(    text=str(len(excl)))

        self._freq_data_cache = freqs
        self._populate_freq_tree(freqs)
        self._populate_alert_tree(critical)

    def _populate_freq_tree(self, freqs: dict):
        self._freq_tree.delete(*self._freq_tree.get_children())
        if self._sort_col == "Código":
            items = sorted(freqs.items(), key=lambda x: x[0],
                           reverse=self._sort_asc)
        else:
            items = sorted(freqs.items(), key=lambda x: x[1],
                           reverse=(not self._sort_asc))
        for code, freq in items:
            critical = freq >= 50
            self._freq_tree.insert(
                "", END,
                values=(code, freq, "⚠ CRÍTICO" if critical else "✓ NORMAL"),
                tags=("critical" if critical else "normal",)
            )

    def _populate_alert_tree(self, critical: list):
        self._alert_tree.delete(*self._alert_tree.get_children())
        for code, freq in sorted(critical, key=lambda x: x[1], reverse=True):
            if freq >= 200:
                level, tag = "🔴 EXTREMO",   "extreme"
            elif freq >= 100:
                level, tag = "🟠 MUY ALTO",  "critical"
            else:
                level, tag = "🟡 ALTO",      "critical"
            self._alert_tree.insert("", END,
                                    values=(code, freq, level), tags=(tag,))

    def _filter_freq_table(self, *_):
        q = self._search_var.get().upper()
        self._populate_freq_tree(
            {k: v for k, v in self._freq_data_cache.items() if q in k}
        )

    def _sort_tree(self, col: str):
        self._sort_asc = (not self._sort_asc) if self._sort_col == col else False
        self._sort_col = col
        self._populate_freq_tree(self._freq_data_cache)

    # ══════════════════════════════════════════
    #  CONSOLA
    # ══════════════════════════════════════════

    def append_log(self, msg: str):
        self._console.text.configure(state="normal")
        self._console.text.insert(END, msg + "\n")
        self._console.text.see(END)
        self._console.text.configure(state="disabled")

    def _clear_console(self):
        self._console.text.configure(state="normal")
        self._console.text.delete("1.0", END)
        self._console.text.configure(state="disabled")

    # ══════════════════════════════════════════
    #  PROGRESO / ESTADO
    # ══════════════════════════════════════════

    def update_progress(self, value: float, label: str = ""):
        self._prog_var.set(value * 100)
        if label:
            self._prog_lbl.configure(text=label)
        self._status_lbl.configure(
            text="✅  Completado" if value >= 1.0 else "⚙️  Procesando..."
        )

    def set_processing_state(self, processing: bool):
        state = DISABLED if processing else NORMAL
        self._btn_load.configure(state=state)
        self._btn_sample.configure(state=state)
        self._status_lbl.configure(
            text="⚙️  Procesando archivos..." if processing else "✅  Listo"
        )

    def show_processing_results(self, results):
        ok     = sum(1 for r in results if r.success)
        fail   = len(results) - ok
        events = sum(r.codes_found for r in results)
        messagebox.showinfo(
            "Procesamiento Completado",
            f"✅  Archivos exitosos : {ok}\n"
            f"❌  Con error         : {fail}\n"
            f"📊  Eventos detectados: {events:,}",
            parent=self
        )

    # ══════════════════════════════════════════
    #  BOTONES → DIÁLOGOS
    # ══════════════════════════════════════════

    def _open_query(self):
        from views.dialogs import QueryDialog
        QueryDialog(self, self._ctrl)

    def _open_top5(self):
        from views.dialogs import Top5Dialog
        Top5Dialog(self, self._ctrl)

    def _open_exclusions(self):
        from views.dialogs import ExclusionsDialog
        ExclusionsDialog(self, self._ctrl)
        self.refresh_stats(None)

    def _generate_audit(self):
        path = self._ctrl.action_generate_audit_report()
        messagebox.showinfo("Reporte Generado",
                            f"Reporte guardado en:\n{path}", parent=self)
        self.append_log(f"[AUDIT] Reporte generado: {path}")

    def _save_state(self):
        self._ctrl.action_save_state()
        messagebox.showinfo("Estado Guardado",
                            "Guardado en: data/respaldo_logs.dat", parent=self)
        self.append_log("[SAVE] Estado guardado manualmente.")

    def _reset_data(self):
        if messagebox.askyesno("Confirmar Reset",
                               "¿Limpiar todos los datos en memoria?", parent=self):
            self._ctrl.action_reset_data()

    def _on_close(self):
        if messagebox.askyesno("Salir",
                               "¿Deseas guardar el estado antes de salir?", parent=self):
            self._ctrl.action_save_and_exit()
        else:
            self.destroy()

    def destroy(self):
        super().destroy()
