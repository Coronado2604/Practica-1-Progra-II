"""
CyberShield - Monitoreo Concurrente de Incidentes de Ciberseguridad
Punto de entrada principal de la aplicación

Ejecutar:
    pip install ttkbootstrap
    python main.py
"""

import os
import sys

# Asegurar que el directorio del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.app_controller import AppController


def main():
    app = AppController()
    app.run()


if __name__ == "__main__":
    main()
