"""
models/incident_model.py
Modelo principal: gestión de frecuencias, Observer, serialización
"""

import os
import pickle
import threading
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# ─────────────────────────────────────────────
#  PATRÓN OBSERVER
# ─────────────────────────────────────────────

class AlertObserver(ABC):
    """Interfaz base para todos los observadores de alertas."""

    @abstractmethod
    def notify(self, code: str, frequency: int):
        pass


class ConsolaAlertaObserver(AlertObserver):
    """Observador que imprime alertas en la consola."""

    def notify(self, code: str, frequency: int):
        msg = (
            f"¡ALERTA DE SEGURIDAD! El evento '{code}' "
            f"ha superado las 50 apariciones críticas. "
            f"[Frecuencia actual: {frequency}]"
        )
        print(msg)
        return msg


class ArchivoAlertaObserver(AlertObserver):
    """Observador que escribe alertas en incidentes_criticos.log."""

    LOG_PATH = os.path.join("logs", "incidentes_criticos.log")

    def __init__(self):
        os.makedirs("logs", exist_ok=True)
        logging.basicConfig(
            filename=self.LOG_PATH,
            level=logging.WARNING,
            format="%(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._logger = logging.getLogger("CyberShield.ArchivoAlerta")

    def notify(self, code: str, frequency: int):
        msg = (
            f"¡ALERTA DE SEGURIDAD! El evento '{code}' "
            f"ha superado las 50 apariciones críticas. "
            f"[Frecuencia actual: {frequency}]"
        )
        self._logger.warning(msg)
        return msg


# ─────────────────────────────────────────────
#  SUJETO OBSERVABLE: MonitorDeIncidentes
# ─────────────────────────────────────────────

class MonitorDeIncidentes:
    """
    Sujeto del patrón Observer.
    Gestiona el mapa global de frecuencias de forma thread-safe.
    """

    BACKUP_PATH = os.path.join("data", "respaldo_logs.dat")
    CRITICAL_THRESHOLD = 50

    def __init__(self):
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        # Mapa global thread-safe
        self._lock = threading.Lock()
        self._freq_map: dict[str, int] = {}
        self._excluded_codes: set[str] = set()
        self._observers: list[AlertObserver] = []
        self._alerted_codes: set[str] = set()   # Para no re-alertar el mismo código

        # Cargar estado persistido si existe
        self._load_state()

        # Registrar observadores predeterminados
        self.add_observer(ConsolaAlertaObserver())
        self.add_observer(ArchivoAlertaObserver())

    # ── Observadores ──────────────────────────

    def add_observer(self, observer: AlertObserver):
        self._observers.append(observer)

    def remove_observer(self, observer: AlertObserver):
        self._observers.remove(observer)

    def _notify_observers(self, code: str, frequency: int):
        for obs in self._observers:
            obs.notify(code, frequency)

    # ── Exclusiones ───────────────────────────

    def add_exclusion(self, code: str):
        with self._lock:
            self._excluded_codes.add(code.strip().upper())

    def remove_exclusion(self, code: str):
        with self._lock:
            self._excluded_codes.discard(code.strip().upper())

    def get_exclusions(self) -> set:
        with self._lock:
            return set(self._excluded_codes)

    def is_excluded(self, code: str) -> bool:
        return code.strip().upper() in self._excluded_codes

    # ── Actualización thread-safe ─────────────

    def update_frequency(self, code: str, count: int = 1):
        code = code.strip().upper()
        if self.is_excluded(code):
            return

        should_alert = False
        current_freq = 0

        with self._lock:
            self._freq_map[code] = self._freq_map.get(code, 0) + count
            current_freq = self._freq_map[code]
            if (
                current_freq >= self.CRITICAL_THRESHOLD
                and code not in self._alerted_codes
            ):
                self._alerted_codes.add(code)
                should_alert = True

        if should_alert:
            self._notify_observers(code, current_freq)

    # ── Consultas ─────────────────────────────

    def get_frequency(self, code: str) -> int:
        with self._lock:
            return self._freq_map.get(code.strip().upper(), 0)

    def get_top_n(self, n: int = 5) -> list[tuple[str, int]]:
        with self._lock:
            sorted_items = sorted(
                self._freq_map.items(), key=lambda x: x[1], reverse=True
            )
        return sorted_items[:n]

    def get_all_sorted_alpha(self) -> list[tuple[str, int]]:
        with self._lock:
            return sorted(self._freq_map.items(), key=lambda x: x[0])

    def get_all_frequencies(self) -> dict:
        with self._lock:
            return dict(self._freq_map)

    def get_total_events(self) -> int:
        with self._lock:
            return sum(self._freq_map.values())

    def get_unique_codes(self) -> int:
        with self._lock:
            return len(self._freq_map)

    def get_critical_codes(self) -> list[tuple[str, int]]:
        """Retorna todos los códigos que superan el umbral crítico."""
        with self._lock:
            return [
                (code, freq)
                for code, freq in self._freq_map.items()
                if freq >= self.CRITICAL_THRESHOLD
            ]

    # ── Persistencia ──────────────────────────

    def save_state(self):
        """Serializa el estado completo en respaldo_logs.dat."""
        state = {
            "freq_map": self._freq_map,
            "excluded_codes": self._excluded_codes,
            "alerted_codes": self._alerted_codes,
        }
        with self._lock:
            with open(self.BACKUP_PATH, "wb") as f:
                pickle.dump(state, f)

    def _load_state(self):
        """Carga el estado serializado si el archivo existe."""
        if os.path.exists(self.BACKUP_PATH):
            try:
                with open(self.BACKUP_PATH, "rb") as f:
                    state = pickle.load(f)
                self._freq_map = state.get("freq_map", {})
                self._excluded_codes = state.get("excluded_codes", set())
                self._alerted_codes = state.get("alerted_codes", set())
            except Exception as e:
                print(f"[WARN] No se pudo cargar respaldo: {e}")

    # ── Reporte de auditoría ───────────────────

    def generate_audit_report(self) -> str:
        path = os.path.join("logs", "reporte_auditoria.txt")
        os.makedirs("logs", exist_ok=True)
        lines = self.get_all_sorted_alpha()
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write("  REPORTE DE AUDITORÍA - CyberShield\n")
            f.write("=" * 50 + "\n\n")
            for code, freq in lines:
                f.write(f"{code}: {freq}\n")
        return path

    def reset(self):
        """Limpia todos los datos en memoria (no el archivo)."""
        with self._lock:
            self._freq_map.clear()
            self._alerted_codes.clear()
