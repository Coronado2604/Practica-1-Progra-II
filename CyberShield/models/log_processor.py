"""
models/log_processor.py
Procesamiento concurrente de archivos de log con ThreadPoolExecutor
"""

import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ProcessingResult:
    """Resultado del procesamiento de un archivo de log."""
    filename: str
    codes_found: int = 0
    lines_processed: int = 0
    errors: list = field(default_factory=list)
    success: bool = True


class LogProcessor:
    """
    Procesa múltiples archivos de log de forma concurrente.
    Actualiza MonitorDeIncidentes de forma thread-safe.
    """

    # Patrón para extraer códigos: palabras en MAYÚSCULAS con guiones bajos
    # Ej: ERR_404, WARN_AUTH_FAIL, ERR_AUTH_FAIL
    CODE_PATTERN = re.compile(r'\b([A-Z][A-Z0-9_]{2,})\b')

    def __init__(self, monitor, max_workers: int = 4):
        self._monitor = monitor
        self._max_workers = max_workers
        self._progress_callback: Callable | None = None
        self._log_callback: Callable | None = None
        self._is_processing = False
        self._lock = threading.Lock()

    def set_progress_callback(self, cb: Callable):
        self._progress_callback = cb

    def set_log_callback(self, cb: Callable):
        self._log_callback = cb

    def _emit_log(self, msg: str):
        if self._log_callback:
            self._log_callback(msg)

    def _emit_progress(self, value: float, label: str = ""):
        if self._progress_callback:
            self._progress_callback(value, label)

    def process_files(self, file_paths: list[str]) -> list[ProcessingResult]:
        """
        Procesa todos los archivos de log de forma concurrente.
        Retorna la lista de resultados por archivo.
        """
        if not file_paths:
            return []

        with self._lock:
            self._is_processing = True

        results = []
        total = len(file_paths)
        completed = 0

        self._emit_log(f"[INICIO] Procesando {total} archivo(s) con hasta {self._max_workers} hilos...")
        self._emit_progress(0.0, "Iniciando procesamiento...")

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                executor.submit(self._process_single_file, path): path
                for path in file_paths
            }

            for future in as_completed(futures):
                path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    progress = completed / total
                    self._emit_progress(
                        progress,
                        f"Procesado: {os.path.basename(path)} ({completed}/{total})"
                    )
                    self._emit_log(
                        f"[OK] {os.path.basename(path)} → "
                        f"{result.codes_found} eventos en {result.lines_processed} líneas"
                    )
                except Exception as e:
                    results.append(ProcessingResult(
                        filename=path, success=False,
                        errors=[str(e)]
                    ))
                    self._emit_log(f"[ERROR] {os.path.basename(path)}: {e}")
                    completed += 1

        with self._lock:
            self._is_processing = False

        self._emit_progress(1.0, "Procesamiento completado")
        self._emit_log(f"[FIN] Procesamiento completado. Total archivos: {total}")
        return results

    def _process_single_file(self, file_path: str) -> ProcessingResult:
        """Procesa un único archivo de log en su propio hilo."""
        result = ProcessingResult(filename=file_path)
        thread_name = threading.current_thread().name

        self._emit_log(
            f"[{thread_name}] Leyendo: {os.path.basename(file_path)}"
        )

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    result.lines_processed += 1
                    codes = self.CODE_PATTERN.findall(line)
                    for code in codes:
                        self._monitor.update_frequency(code)
                        result.codes_found += 1
        except FileNotFoundError:
            result.success = False
            result.errors.append(f"Archivo no encontrado: {file_path}")
        except PermissionError:
            result.success = False
            result.errors.append(f"Sin permisos para leer: {file_path}")
        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def generate_sample_logs(self, output_dir: str, num_files: int = 3) -> list[str]:
        """
        Genera archivos de log de ejemplo para demostración.
        Retorna la lista de paths creados.
        """
        import random

        os.makedirs(output_dir, exist_ok=True)

        event_codes = [
            "ERR_AUTH_FAIL", "ERR_404", "ERR_500", "ERR_TIMEOUT",
            "WARN_BRUTE_FORCE", "WARN_SQL_INJECT", "ERR_FIREWALL_BLOCK",
            "INFO_LOGIN_OK", "ERR_DDOS_DETECTED", "WARN_SUSPICIOUS_IP",
            "ERR_CERT_EXPIRED", "WARN_PORT_SCAN", "ERR_PAYLOAD_INVALID",
            "INFO_SCAN_COMPLETE", "ERR_ACCESS_DENIED", "WARN_MALWARE_DETECTED",
            "ERR_XSS_ATTEMPT", "WARN_PRIVILEGE_ESCALATION",
        ]

        safe_codes = ["INFO_LOGIN_OK", "INFO_SCAN_COMPLETE"]
        # Agregar exclusiones seguras al monitor
        for sc in safe_codes:
            self._monitor.add_exclusion(sc)

        paths = []
        for i in range(1, num_files + 1):
            path = os.path.join(output_dir, f"servidor{i}.log")
            with open(path, "w", encoding="utf-8") as f:
                for _ in range(random.randint(300, 600)):
                    code = random.choice(event_codes)
                    ip = f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
                    port = random.choice([22, 80, 443, 3306, 8080])
                    f.write(
                        f"[{_:04d}] HOST={ip} PORT={port} EVENT={code} "
                        f"SEVERITY={'HIGH' if 'ERR' in code else 'LOW'}\n"
                    )
            paths.append(path)
            self._emit_log(f"[GEN] Creado: {os.path.basename(path)}")

        return paths

    @property
    def is_processing(self) -> bool:
        with self._lock:
            return self._is_processing
