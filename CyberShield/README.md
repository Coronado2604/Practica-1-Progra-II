# ⚡ CyberShield — Monitoreo Concurrente de Incidentes de Ciberseguridad

> Práctica 1 — Programación II · UNET · Departamento de Informática

---

## Estructura del Proyecto (MVC)

```
CyberShield/
│
├── main.py                        ← Punto de entrada
├── requirements.txt
│
├── controllers/
│   ├── __init__.py
│   └── app_controller.py          ← Controlador principal (orquesta Model ↔ View)
│
├── models/
│   ├── __init__.py
│   ├── incident_model.py          ← MonitorDeIncidentes + Observers + Serialización
│   └── log_processor.py          ← Procesamiento concurrente con ThreadPoolExecutor
│
├── views/
│   ├── __init__.py
│   ├── main_view.py               ← Ventana principal (ttkbootstrap, tema darkly)
│   └── dialogs.py                 ← Diálogos: Consulta, Top5, Exclusiones
│
├── logs/                          ← Generado automáticamente
│   ├── incidentes_criticos.log   ← Alertas críticas (ArchivoAlertaObserver)
│   ├── reporte_auditoria.txt     ← Reporte alfabético
│   └── samples/                  ← Logs de muestra generados
│
├── data/                          ← Generado automáticamente
│   └── respaldo_logs.dat         ← Estado serializado (pickle)
│
└── .vscode/
    └── launch.json               ← Configuración para ejecutar desde VSCode
```

---

## Instalación

```bash
# 1. Instalar dependencias
pip install ttkbootstrap

# 2. Ejecutar
python main.py
```

---

## Cómo usar en VSCode

1. Abrir la carpeta `CyberShield/` en VSCode (`File → Open Folder`)
2. Instalar la extensión **Python** (Microsoft)
3. Presionar **F5** para ejecutar (usa la configuración `.vscode/launch.json`)
4. O desde la terminal integrada: `python main.py`

---

## Requisitos Funcionales Implementados

| # | Requisito | Implementación |
|---|-----------|----------------|
| 1 | Procesamiento concurrente de logs | `ThreadPoolExecutor` en `LogProcessor` |
| 2 | Gestión centralizada con bloqueo | `ConcurrentHashMap` → `dict` + `threading.Lock` en `MonitorDeIncidentes` |
| 3 | Persistencia con serialización | `pickle` → `respaldo_logs.dat` (carga al inicio, guarda al salir) |
| 4 | Patrón Observer | `MonitorDeIncidentes` (sujeto) + `ConsolaAlertaObserver` + `ArchivoAlertaObserver` |
| 5 | Menú interactivo | GUI completa con ttkbootstrap: consulta, Top 5, auditoría, exclusiones |

---

## Flujo de Uso

1. **Generar Logs de Muestra** → crea `servidor1.log`, `servidor2.log`, `servidor3.log`  
   *(o carga tus propios archivos con "Cargar Archivos .log")*
2. El sistema procesa los archivos **en paralelo** (4 hilos)
3. Consulta frecuencias, revisa alertas críticas, genera el reporte
4. Al salir, el estado se **serializa automáticamente**; la próxima ejecución lo carga

---

## Patrón Observer en acción

Cuando un código supera **50 apariciones**:
- `ConsolaAlertaObserver` → imprime en consola
- `ArchivoAlertaObserver` → escribe en `logs/incidentes_criticos.log`

---

## Notas técnicas

- **Thread-safety**: `threading.Lock` protege el `dict` de frecuencias
- **Exclusiones seguras**: `INFO_LOGIN_OK`, `INFO_SCAN_COMPLETE` son ignorados por defecto
- **Persistencia**: si `data/respaldo_logs.dat` existe al iniciar, se cargan los datos anteriores
- **Umbral crítico**: configurable en `MonitorDeIncidentes.CRITICAL_THRESHOLD` (default: 50)
