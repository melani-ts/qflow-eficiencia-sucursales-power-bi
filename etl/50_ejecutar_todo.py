"""Ejecuta todo el proceso ETL en orden: limpieza de cada tabla, creacion del schema, carga y auditorias.

Cada paso se detiene si falla (los scripts tienen controles con assert y la carga corre en modo estricto).
Uso: python 50_ejecutar_todo.py
"""
import subprocess
import sys
import time
from pathlib import Path

PASOS = [
    "01_diccionarios.py",       # diccionarios primero: los usan clientes y hechos
    "02_dt_branch.py",
    "03_dt_service.py",
    "04_dt_classification.py",
    "05_dt_officer.py",
    "06_dt_function.py",
    "07_dt_customer.py",        # necesita los diccionarios limpios
    "08_fact_oficial_hora.py",
    "20_dim_fecha_hora.py",
    "09_fact_proceso.py",       # necesita dim_service, dim_officer y dim_classification limpias
    "31_cargar_mysql.py",       # recrea el schema qflow, carga y verifica conteos y sumas
    "41_auditar_tipos.py",
    "43_auditar_linaje.py",
]

if __name__ == "__main__":
    carpeta = Path(__file__).parent
    for paso in PASOS:
        inicio = time.time()
        print(f"=== {paso}", flush=True)
        r = subprocess.run([sys.executable, str(carpeta / paso)], cwd=carpeta)
        if r.returncode != 0:
            sys.exit(f"Fallo {paso}: se detiene el proceso")
        print(f"    listo en {time.time() - inicio:,.0f} s", flush=True)
    print("ETL completo")
