"""Perfil de calidad de una tabla original, columna por columna.

Uso: python 00_perfilar.py <nombre_csv_sin_extension> [<otro> ...]
"""
import sys

import numpy as np
import pandas as pd

from config import leer


def perfil_columna(s):
    fila = {
        "nulos": int(s.isna().sum()),
        "%nulos": round(100 * s.isna().mean(), 2),
        "distintos": int(s.nunique()),
    }
    no_nulos = s.dropna()
    fila["con_espacios_extra"] = int((no_nulos != no_nulos.str.strip()).sum())
    fila["solo_espacios"] = int((no_nulos.str.strip() == "").sum())
    num = pd.to_numeric(no_nulos, errors="coerce")
    fila["no_numericos"] = int(num.isna().sum())
    if num.notna().mean() > 0.95 and len(num.dropna()):
        n = num.dropna()
        q1, q3 = n.quantile([0.25, 0.75])
        iqr = q3 - q1
        fila.update({
            "min": n.min(), "p1": n.quantile(0.01), "p25": q1, "mediana": n.median(),
            "p75": q3, "p99": n.quantile(0.99), "p99.9": n.quantile(0.999), "max": n.max(),
            "negativos": int((n < 0).sum()), "ceros": int((n == 0).sum()),
            "atip_1.5IQR": int(((n < q1 - 1.5 * iqr) | (n > q3 + 1.5 * iqr)).sum()),
            "atip_3IQR": int(((n < q1 - 3 * iqr) | (n > q3 + 3 * iqr)).sum()),
        })
    return fila


def perfilar(nombre, top=12):
    df = leer(nombre)
    print(f"\n==================== {nombre}: {len(df):,} filas x {df.shape[1]} columnas")
    print(f"filas duplicadas completas: {df.duplicated().sum():,}")
    tabla = pd.DataFrame({c: perfil_columna(df[c]) for c in df.columns}).T
    with pd.option_context("display.max_columns", None, "display.width", 250,
                           "display.float_format", "{:,.2f}".format):
        print(tabla)
    for c in df.columns:
        if df[c].nunique() <= 40:
            vc = df[c].value_counts(dropna=False).head(top)
            print(f"\n-- {c}: " + ", ".join(f"{k!r}={v:,}" for k, v in vc.items()))
    return df


if __name__ == "__main__":
    for nombre in sys.argv[1:]:
        perfilar(nombre)
