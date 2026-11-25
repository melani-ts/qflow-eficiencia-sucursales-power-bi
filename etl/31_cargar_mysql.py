"""Crea el schema qflow y carga los CSV limpios. Verifica conteos y sumas de control.

Orden: diccionarios, dimensiones, hechos, puente (las FK existen antes de cargar, asi una fila sin
correspondencia hace fallar la carga en vez de perderse).
"""
import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pymysql

from config import LIMPIO, MYSQL

MYSQL_EXE = os.getenv("QFLOW_MYSQL_EXE", r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe")
DDL = Path(__file__).with_name("30_crear_schema.sql")

ORDEN = ["dic_action", "dic_backofficetask", "dic_customer_level", "dic_sublevel", "dic_occupation",
         "dic_marital_status", "dic_housing_type", "dic_education_level", "dic_officer_status",
         "dic_proc_status", "dic_resolution", "dic_signoutreason",
         "dim_branch", "dim_service", "dim_customer", "dim_officer", "dim_classification",
         "dim_date", "dim_hour", "dim_function_s", "dim_function_l",
         "fact_proceso", "bridge_process_classification", "fact_oficial_hora"]

SUMAS = {
    "fact_proceso": ["wait_sec", "service_sec", "hold_sec", "n_calls", "n_transfers", "is_abandoned",
                     "total_time_sec"],
    "fact_oficial_hora": ["duration_sec", "duration_sec_capped", "n_events", "n_officers"],
}


def conectar(**extra):
    return pymysql.connect(host=MYSQL["host"], port=MYSQL["port"], user=MYSQL["user"],
                           password=MYSQL["password"], charset="utf8mb4", **extra)


def carpeta_segura():
    with conectar() as c, c.cursor() as cur:
        cur.execute("SELECT @@secure_file_priv")
        return cur.fetchone()[0]


def crear_schema():
    subprocess.run([MYSQL_EXE, f"-u{MYSQL['user']}", f"-p{MYSQL['password']}", "-e", f"source {DDL.as_posix()}"],
                   check=True)


def cargar(tabla, cur, ruta_servidor, local):
    columnas = pd.read_csv(LIMPIO / f"{tabla}.csv", nrows=0).columns
    cur.execute(f"""
        LOAD DATA {'LOCAL' if local else ''} INFILE '{ruta_servidor}' INTO TABLE {tabla}
        CHARACTER SET utf8mb4
        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '\\\\'
        LINES TERMINATED BY '\\n' IGNORE 1 LINES ({', '.join(f'`{c}`' for c in columnas)})""")
    cur.execute("SHOW WARNINGS LIMIT 5")
    avisos = cur.fetchall()
    if avisos:
        raise RuntimeError(f"{tabla}: avisos en la carga {avisos}")


if __name__ == "__main__":
    crear_schema()
    destino = carpeta_segura()
    local = not destino
    with conectar(database=MYSQL["database"], local_infile=local, autocommit=True) as con, con.cursor() as cur:
        cur.execute("SET SESSION sql_mode = 'STRICT_ALL_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE'")
        for tabla in ORDEN:
            origen = LIMPIO / f"{tabla}.csv"
            if local:
                ruta = origen.as_posix()
            else:
                copia = Path(destino) / origen.name
                shutil.copyfile(origen, copia)
                ruta = copia.as_posix()
            cargar(tabla, cur, ruta, local)
            if not local:
                copia.unlink()
            filas_csv = sum(1 for _ in open(origen, encoding="utf-8")) - 1
            cur.execute(f"SELECT COUNT(*) FROM {tabla}")
            filas_db = cur.fetchone()[0]
            estado = "OK" if filas_csv == filas_db else "DIFERENCIA"
            print(f"{tabla:30s} csv {filas_csv:>10,}  mysql {filas_db:>10,}  {estado}")
            assert filas_csv == filas_db

        print("\nSumas de control (CSV limpio vs MySQL)")
        for tabla, cols in SUMAS.items():
            csv = pd.read_csv(LIMPIO / f"{tabla}.csv", usecols=cols, na_values=[r"\N"], keep_default_na=False)
            cur.execute(f"SELECT {', '.join(f'SUM({c})' for c in cols)} FROM {tabla}")
            db = cur.fetchone()
            for c, v in zip(cols, db):
                a, b = round(float(csv[c].sum()), 3), round(float(v), 3)
                print(f"  {tabla}.{c:20s} csv {a:>18,.3f}  mysql {b:>18,.3f}  {'OK' if a == b else 'DIFERENCIA'}")
                assert a == b
