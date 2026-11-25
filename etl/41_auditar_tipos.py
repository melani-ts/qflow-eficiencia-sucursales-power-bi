"""Revisa que el tipo de dato de cada columna de qflow corresponda a su contenido real.

Para cada columna compara el tipo declarado con: minimo, maximo, decimales, longitud maxima y si un
texto contiene solo numeros. Imprime las columnas sospechosas.
"""
import pandas as pd
import pymysql

from config import MYSQL

RANGO_ENTERO = {"tinyint": (-128, 127), "smallint": (-32768, 32767), "int": (-2**31, 2**31 - 1),
                "bigint": (-2**63, 2**63 - 1)}

if __name__ == "__main__":
    con = pymysql.connect(host=MYSQL["host"], user=MYSQL["user"], password=MYSQL["password"],
                          database=MYSQL["database"], charset="utf8mb4")
    cols = pd.read_sql("""SELECT table_name t, column_name c, data_type tipo, column_type tipo_completo,
                                 character_maximum_length largo, is_nullable nulo
                          FROM information_schema.columns WHERE table_schema = 'qflow'
                          ORDER BY table_name, ordinal_position""", con)
    filas = []
    for t, g in cols.groupby("t"):
        partes = []
        for _, r in g.iterrows():
            c = f"`{r.c}`"
            if r.tipo in RANGO_ENTERO or r.tipo == "decimal":
                partes += [f"MIN({c})", f"MAX({c})", f"COUNT(DISTINCT {c})",
                           f"SUM({c} <> ROUND({c}))" if r.tipo == "decimal" else "0"]
            elif r.tipo in ("varchar", "char"):
                partes += [f"MAX(CHAR_LENGTH({c}))", f"SUM({c} NOT REGEXP '^-?[0-9]+$')", f"COUNT(DISTINCT {c})", "0"]
            else:
                partes += [f"MIN({c})", f"MAX({c})", f"COUNT(DISTINCT {c})", "0"]
        partes.append("COUNT(*)")
        with con.cursor() as cur:
            cur.execute(f"SELECT {', '.join(partes)} FROM {t}")
            v = cur.fetchone()
        total = v[-1]
        for i, (_, r) in enumerate(g.iterrows()):
            a, b, distintos, extra = v[4 * i: 4 * i + 4]
            filas.append(dict(tabla=t, columna=r.c, tipo=r.tipo_completo, a=a, b=b, distintos=distintos,
                              extra=extra, total=total, largo=r.largo))
    df = pd.DataFrame(filas)

    avisos = []
    for _, r in df.iterrows():
        tipo = r.tipo.split("(")[0]
        if tipo in RANGO_ENTERO and r.a is not None:
            lo, hi = RANGO_ENTERO[tipo]
            if r.a < lo or r.b > hi:
                avisos.append((r.tabla, r.columna, r.tipo, f"fuera de rango {r.a}..{r.b}"))
            if tipo != "tinyint" and r.a >= 0 and r.b <= 1 and r.distintos <= 2 and not r.columna.endswith("_id"):
                avisos.append((r.tabla, r.columna, r.tipo, "solo 0/1: deberia ser TINYINT (booleano)"))
        if tipo == "decimal" and r.extra == 0 and r.a is not None:
            avisos.append((r.tabla, r.columna, r.tipo, "decimal sin decimales: podria ser entero"))
        if tipo in ("varchar", "char") and r.a is not None:
            if r.b == 0:
                avisos.append((r.tabla, r.columna, r.tipo, f"texto que solo contiene numeros (largo max {r.a})"))
            if r.largo and r.a > r.largo:
                avisos.append((r.tabla, r.columna, r.tipo, "texto mas largo que la columna"))
    with pd.option_context("display.width", 250, "display.max_rows", 400, "display.max_colwidth", 60):
        print(df[["tabla", "columna", "tipo", "a", "b", "distintos"]].to_string(index=False))
        print("\n=== AVISOS ===")
        print(pd.DataFrame(avisos, columns=["tabla", "columna", "tipo", "aviso"]).to_string(index=False))
