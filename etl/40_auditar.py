"""Auditoria critica del schema qflow ya cargado: lee cada tabla desde MySQL y revisa columna por columna.

Salida: perfil por columna (nulos, distintos, texto no normalizado, rangos, atipicos) en
auditoria_columnas.csv y hallazgos puntuales impresos en pantalla.
"""
import re
import unicodedata
import warnings

import numpy as np
import pandas as pd
import pymysql

from config import BASE, MYSQL

warnings.filterwarnings("ignore")
MOJIBAKE = re.compile(r"[ÃÂ�#]|\?")


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


def perfil(tabla, df):
    filas = []
    for c in df.columns:
        s = df[c]
        f = {"tabla": tabla, "columna": c, "tipo": str(s.dtype), "filas": len(s),
             "nulos": int(s.isna().sum()), "%nulos": round(100 * s.isna().mean(), 2), "distintos": int(s.nunique())}
        nn = s.dropna()
        if len(nn) and isinstance(nn.iloc[0], str):
            nn = nn.astype(str)
            f["espacios_borde"] = int((nn != nn.str.strip()).sum())
            f["dobles_espacios"] = int(nn.str.contains("  ").sum())
            f["vacios"] = int((nn.str.strip() == "").sum())
            f["caracteres_raros"] = int(nn.str.contains(MOJIBAKE).sum())
            # valores distintos que solo difieren en mayusculas, tildes o espacios
            u = pd.Series(nn.unique())
            grupos = u.groupby(u.map(sin_tildes)).agg(list)
            variantes = [v for v in grupos if len(v) > 1]
            f["variantes_grafia"] = "; ".join(" | ".join(v) for v in variantes[:5])
        elif pd.api.types.is_numeric_dtype(s) and len(nn):
            x = nn.astype(float)
            q1, q3 = x.quantile([.25, .75])
            iqr = q3 - q1
            f.update(min=x.min(), p1=x.quantile(.01), mediana=x.median(), p99=x.quantile(.99), max=x.max(),
                     negativos=int((x < 0).sum()), ceros=int((x == 0).sum()),
                     atip_3iqr=int(((x < q1 - 3 * iqr) | (x > q3 + 3 * iqr)).sum()) if iqr > 0 else 0)
        filas.append(f)
    return filas


if __name__ == "__main__":
    con = pymysql.connect(host=MYSQL["host"], user=MYSQL["user"], password=MYSQL["password"],
                          database=MYSQL["database"], charset="utf8mb4")
    tablas = pd.read_sql("SELECT table_name AS t FROM information_schema.tables WHERE table_schema='qflow'", con).t
    todo, datos = [], {}
    for t in tablas:
        df = pd.read_sql(f"SELECT * FROM {t}", con)
        datos[t] = df
        todo += perfil(t, df)
        print(f"leida {t}: {len(df):,}")
    out = pd.DataFrame(todo)
    out.to_csv(BASE / "Limpieza" / "auditoria_columnas.csv", index=False, encoding="utf-8-sig")
    pd.to_pickle(datos, BASE / "Limpieza" / "_auditoria_datos.pkl")
    cols = ["tabla", "columna", "nulos", "%nulos", "distintos", "espacios_borde", "dobles_espacios",
            "caracteres_raros", "variantes_grafia"]
    texto = out[out.espacios_borde.notna()][cols]
    with pd.option_context("display.width", 300, "display.max_colwidth", 120, "display.max_rows", 500):
        print(texto[(texto.espacios_borde > 0) | (texto.dobles_espacios > 0) | (texto.caracteres_raros > 0)
                    | (texto.variantes_grafia != "")].to_string(index=False))
        num = ["tabla", "columna", "nulos", "%nulos", "min", "p1", "mediana", "p99", "max", "negativos", "ceros", "atip_3iqr"]
        print(out[out["min"].notna()][num].to_string(index=False))
