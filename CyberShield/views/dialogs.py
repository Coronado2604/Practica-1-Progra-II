"""
views/dialogs.py
Ventanas de diálogo: consulta, top5, exclusiones
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText

FONT_MONO   = ("Consolas", 10)
FONT_HEADER = ("Consolas", 12, "bold")
FONT_SMALL  = ("Consolas", 9)
FONT_BIG    = ("Consolas", 26, "bold")


class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title_text: str, size=(500, 380)):
        super().__init__(parent)
        self.title(f"⚡ CyberShield — {title_text}")
        self.geometry(f"{size[0]}x{size[1]}")
        self.resizable(True, True)
        self.configure(bg="#0d1117")
        self.transient(parent)
        self.grab_set()

        hdr = tk.Frame(self, bg="#0d1117", pady=10, padx=15)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=title_text, font=FONT_HEADER,
                 fg="#00ff41", bg="#0d1117").pack(anchor=tk.W)
        ttk.Separator(self, orient=HORIZONTAL).pack(fill=tk.X)

        self.body = ttk.Frame(self, padding=15)
        self.body.pack(fill=tk.BOTH, expand=True)


# ══════════════════════════════════════════════════════════

class QueryDialog(BaseDialog):
    def __init__(self, parent, controller):
        super().__init__(parent, "🔍  CONSULTAR FRECUENCIA DE CÓDIGO", (500, 310))
        self._ctrl = controller
        self._build()

    def _build(self):
        b = self.body
        ttk.Label(b, text="Código de evento (ej: ERR_AUTH_FAIL):",
                  font=FONT_SMALL, bootstyle="secondary").pack(anchor=tk.W)

        row = ttk.Frame(b)
        row.pack(fill=tk.X, pady=6)
        self._var = tk.StringVar()
        e = ttk.Entry(row, textvariable=self._var, font=("Consolas", 13),
                      bootstyle="success", width=26)
        e.pack(side=tk.LEFT, padx=(0, 8))
        e.focus()
        e.bind("<Return>", lambda _: self._query())
        ttk.Button(row, text="BUSCAR", bootstyle="success",
                   command=self._query, width=12).pack(side=tk.LEFT)

        ttk.Separator(b, orient=HORIZONTAL).pack(fill=tk.X, pady=10)

        res = ttk.Frame(b, bootstyle="dark", padding=12)
        res.pack(fill=tk.BOTH, expand=True)

        ttk.Label(res, text="Código:", font=FONT_SMALL,
                  bootstyle="secondary").grid(row=0, column=0, sticky=tk.W)
        self._lbl_code = ttk.Label(res, text="—",
                                   font=("Consolas", 13, "bold"), bootstyle="info")
        self._lbl_code.grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(res, text="Frecuencia:", font=FONT_SMALL,
                  bootstyle="secondary").grid(row=1, column=0, sticky=tk.W, pady=6)
        self._lbl_freq = ttk.Label(res, text="—", font=FONT_BIG, bootstyle="success")
        self._lbl_freq.grid(row=1, column=1, sticky=tk.W, padx=10)

        self._lbl_status = ttk.Label(res, text="", font=FONT_SMALL, bootstyle="warning")
        self._lbl_status.grid(row=2, column=0, columnspan=2, pady=4)

    def _query(self):
        code = self._var.get().strip()
        if not code:
            return
        rcode, freq = self._ctrl.action_query_frequency(code)
        self._lbl_code.configure(text=rcode)
        self._lbl_freq.configure(text=f"{freq:,}")
        if freq == 0:
            self._lbl_status.configure(text="Sin registros para este código.",
                                       bootstyle="secondary")
        elif freq >= 50:
            self._lbl_status.configure(text="⚠ ALERTA: Umbral crítico superado!",
                                       bootstyle="danger")
        else:
            self._lbl_status.configure(text="✓ Frecuencia dentro del rango normal",
                                       bootstyle="success")


# ══════════════════════════════════════════════════════════

class Top5Dialog(BaseDialog):
    def __init__(self, parent, controller):
        super().__init__(parent, "🏆  TOP 5 INCIDENTES MÁS FRECUENTES", (520, 430))
        self._ctrl = controller
        self._build()

    def _build(self):
        b = self.body
        top5 = self._ctrl.action_get_top5()

        if not top5:
            ttk.Label(b, text="No hay datos procesados aún.",
                      font=FONT_MONO, bootstyle="secondary").pack(pady=40)
            return

        max_freq = top5[0][1] if top5 else 1
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        for i, (code, freq) in enumerate(top5):
            pct   = (freq / max_freq) * 100 if max_freq > 0 else 0
            color = "danger" if freq >= 50 else "success"

            row = ttk.Frame(b)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=medals[i], font=("Consolas", 18)).pack(side=tk.LEFT)
            ttk.Label(row, text=f"  {code}", font=("Consolas", 12, "bold"),
                      bootstyle=color).pack(side=tk.LEFT)
            ttk.Label(row, text=f"{freq:,}", font=("Consolas", 15, "bold"),
                      bootstyle=color).pack(side=tk.RIGHT)

            ttk.Progressbar(b, value=pct, bootstyle=f"{color}-striped",
                            length=480).pack(fill=tk.X, padx=6, pady=(0, 6))


# ══════════════════════════════════════════════════════════

class ExclusionsDialog(BaseDialog):
    def __init__(self, parent, controller):
        super().__init__(parent, "🚫  GESTIÓN DE EXCLUSIONES SEGURAS", (500, 470))
        self._ctrl = controller
        self._build()

    def _build(self):
        b = self.body
        ttk.Label(b, text="Agregar código a exclusiones seguras (no se contará):",
                  font=FONT_SMALL, bootstyle="secondary").pack(anchor=tk.W)

        add_row = ttk.Frame(b)
        add_row.pack(fill=tk.X, pady=6)
        self._add_var = tk.StringVar()
        e = ttk.Entry(add_row, textvariable=self._add_var, font=FONT_MONO,
                      bootstyle="warning", width=28)
        e.pack(side=tk.LEFT, padx=(0, 8))
        e.bind("<Return>", lambda _: self._add())
        ttk.Button(add_row, text="+ AGREGAR", bootstyle="warning",
                   command=self._add, width=12).pack(side=tk.LEFT)

        ttk.Separator(b, orient=HORIZONTAL).pack(fill=tk.X, pady=8)
        ttk.Label(b, text="Códigos excluidos actualmente:",
                  font=FONT_SMALL, bootstyle="secondary").pack(anchor=tk.W)

        lf = ttk.Frame(b)
        lf.pack(fill=tk.BOTH, expand=True, pady=4)

        sb = ttk.Scrollbar(lf, bootstyle="warning-round")
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox = tk.Listbox(
            lf, font=FONT_MONO, bg="#0d1117", fg="#ffcc00",
            selectbackground="#2a2000", height=10, yscrollcommand=sb.set
        )
        self._listbox.pack(fill=tk.BOTH, expand=True)
        sb.configure(command=self._listbox.yview)

        ttk.Button(b, text="🗑  ELIMINAR SELECCIONADO",
                   bootstyle="danger-outline", command=self._remove).pack(pady=6)

        self._refresh()

    def _add(self):
        code = self._add_var.get().strip()
        if code and self._ctrl.action_add_exclusion(code):
            self._add_var.set("")
            self._refresh()

    def _remove(self):
        sel = self._listbox.curselection()
        if sel:
            self._ctrl.action_remove_exclusion(self._listbox.get(sel[0]))
            self._refresh()

    def _refresh(self):
        self._listbox.delete(0, tk.END)
        for code in sorted(self._ctrl.action_get_exclusions()):
            self._listbox.insert(tk.END, code)
