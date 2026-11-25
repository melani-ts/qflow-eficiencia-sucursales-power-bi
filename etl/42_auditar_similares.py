"""Busca valores parecidos que podrian significar lo mismo en todas las columnas de texto de las
dimensiones y diccionarios cargados en MySQL.

Criterios (cualquiera marca el par como candidato):
- iguales al quitar tildes, mayusculas, puntuacion y espacios;
- iguales al quitar plurales simples (s/es finales) por palabra;
- uno contiene todas las palabras del otro (subconjunto de palabras);
- similitud de texto (difflib) >= 0.80.
"""
import itertools
import re
import unicodedata
import warnings
from difflib import SequenceMatcher

import pandas as pd
import pymysql

from config import MYSQL

warnings.filterwarnings("ignore")
VACIAS = {"de", "del", "la", "el", "y", "o", "en", "a", "los", "las", "por", "con", "para"}


def base(v):
    v = "".join(c for c in unicodedata.normalize("NFD", v) if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9 ]", " ", v)


def palabras(v):
    return {re.sub(r"(es|s)$", "", p) for p in base(v).split() if p not in VACIAS}


if __name__ == "__main__":
    con = pymysql.connect(host=MYSQL["host"], user=MYSQL["user"], password=MYSQL["password"],
                          database=MYSQL["database"], charset="utf8mb4")
    cols = pd.read_sql("""SELECT table_name t, column_name c FROM information_schema.columns
                          WHERE table_schema='qflow' AND data_type IN ('varchar','char')
                            AND (table_name LIKE 'dim%%' OR table_name LIKE 'dic%%')
                            AND column_name NOT LIKE '%%original' AND column_name NOT IN
                                ('label','mnemonic','year_month_key','classifications')""", con)
    filas = []
    for _, r in cols.iterrows():
        vals = pd.read_sql(f"SELECT `{r.c}` v, COUNT(*) n FROM {r.t} WHERE `{r.c}` IS NOT NULL GROUP BY 1", con)
        if len(vals) > 400 or len(vals) < 2:
            continue
        n = dict(zip(vals.v, vals.n))
        for a, b in itertools.combinations(sorted(n), 2):
            if re.fullmatch(r"[A-Z0-9/ ]{1,4}", a) and re.fullmatch(r"[A-Z0-9/ ]{1,4}", b):
                continue  # codigos cortos
            pa, pb = palabras(a), palabras(b)
            razones = []
            if base(a).split() == base(b).split():
                razones.append("igual sin tildes/mayusculas")
            elif pa == pb:
                razones.append("mismas palabras (plural)")
            elif pa and pb and (pa < pb or pb < pa):
                razones.append("subconjunto de palabras")
            ratio = SequenceMatcher(None, base(a), base(b)).ratio()
            if ratio >= 0.8 and not razones:
                razones.append(f"similitud {ratio:.2f}")
            if razones:
                filas.append(dict(tabla=r.t, columna=r.c, valor_a=a, n_a=n[a], valor_b=b, n_b=n[b],
                                  razon=", ".join(razones)))
    out = pd.DataFrame(filas)
    with pd.option_context("display.width", 250, "display.max_rows", 500, "display.max_colwidth", 55):
        print(out.to_string(index=False) if len(out) else "sin candidatos")
