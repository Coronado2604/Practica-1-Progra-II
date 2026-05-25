"""
controllers/app_controller.py
Controlador principal: orquesta Model ↔ View
"""

import threading
import os
from tkinter import filedialog, messagebox

from models.incident_model import MonitorDeIncidentes
from models.log_processor import LogProcessor


class AppController:
    """
    Controlador central de CyberShield.
    Importa la vista después de que ttkbootstrap crea la ventana.
    """

    def __init__(self):
        # ── Modelo ────────────────────────────
        self._monitor = MonitorDeIncidentes()
        self._processor = LogProcessor(self._monitor, max_workers=4)

        # ── Vista (crea ttk.Window internamente) ─
        from views.main_view import MainView
        self._view = MainView(self)

        # Conectar callbacks del procesador a la vista
        self._processor.set_progress_callback(self._on_progress)
        self._processor.set_log_callback(self._on_log)

        # Estado inicial
        self._view.refresh_stats(self._monitor)

    def run(self):
        self._view.mainloop()

    # ─────────────────────────────────────────
    #  ACCIONES INVOCADAS DESDE LA VISTA
    # ─────────────────────────────────────────

    def action_select_and_process_files(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar archivos de log",
            filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")],
        )
        if paths:
            self._run_processing_thread(list(paths))

    def action_generate_and_process_samples(self):
        log_dir = os.path.join("logs", "samples")
        paths = self._processor.generate_sample_logs(log_dir, num_files=3)
        self._run_processing_thread(paths)

    def action_query_frequency(self, code: str) -> tuple:
        freq = self._monitor.get_frequency(code)
        return code.upper(), freq

    def action_get_top5(self) -> list:
        return self._monitor.get_top_n(5)

    def action_generate_audit_report(self) -> str:
        return self._monitor.generate_audit_report()

    def action_save_and_exit(self):
        self._monitor.save_state()
        self._view.destroy()

    def action_add_exclusion(self, code: str) -> bool:
        if code.strip():
            self._monitor.add_exclusion(code.strip())
            return True
        return False

    def action_remove_exclusion(self, code: str):
        self._monitor.remove_exclusion(code.strip())

    def action_get_exclusions(self) -> set:
        return self._monitor.get_exclusions()

    def action_get_all_frequencies(self) -> dict:
        return self._monitor.get_all_frequencies()

    def action_get_critical_codes(self) -> list:
        return self._monitor.get_critical_codes()

    def action_save_state(self):
        self._monitor.save_state()

    def action_reset_data(self):
        self._monitor.reset()
        self._view.refresh_stats(self._monitor)
        self._on_log("[RESET] Datos en memoria limpiados.")

    # ─────────────────────────────────────────
    #  PROCESAMIENTO EN HILO SECUNDARIO
    # ─────────────────────────────────────────

    def _run_processing_thread(self, paths: list):
        self._view.set_processing_state(True)

        def task():
            results = self._processor.process_files(paths)
            self._view.after(0, self._on_processing_done, results)

        threading.Thread(target=task, daemon=True).start()

    def _on_processing_done(self, results):
        self._view.set_processing_state(False)
        self._view.refresh_stats(self._monitor)
        self._view.show_processing_results(results)
        self._monitor.save_state()
        self._on_log("[AUTO-SAVE] Estado guardado en respaldo_logs.dat")

    def _on_progress(self, value: float, label: str = ""):
        self._view.after(0, self._view.update_progress, value, label)

    def _on_log(self, msg: str):
        self._view.after(0, self._view.append_log, msg)
