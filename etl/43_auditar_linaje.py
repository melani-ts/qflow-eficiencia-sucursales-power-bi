"""Linaje: compara cada columna de cada CSV fuente con su columna en el CSV limpio (identico a MySQL
por las sumas de control). Para cada columna informa si se conserva, cuantas celdas cambiaron y si el
valor original sigue disponible en otra columna. Detecta columnas de la fuente que no llegaron al modelo.
"""
import pandas as pd

from config import LIMPIO, RENOMBRAR, leer

# tabla fuente -> (tabla limpia, clave de union fuente, clave limpia)
TABLAS = {
    "dt_branch": ("dim_branch", "qf_branch_id", "qf_branch_id"),
    "dt_service": ("dim_service", "service_id", "service_id"),
    "dt_customer": ("dim_customer", "customer_id", "customer_id"),
    "dt_officer": ("dim_officer", "officer_id", "officer_id"),
    "dt_classification": ("dim_classification", "classification_id", "classification_id"),
    "dt_function_s": ("dim_function_s", "function_id", "function_id"),
    "fact_oficial_hora": ("fact_oficial_hora", None, None),
    "fact_proceso": ("fact_proceso", "process_id", "process_id"),
}
# columnas renombradas dentro de un script (no por RENOMBRAR)
EXTRA = {("dt_classification", "classificationgroup_id"): "classification_group_ids"}
ELIMINADAS = {("dt_service", c) for c in ["customerpatience", "maxlockduration", "oncallagainmessagetype"]}


def final(c):
    while c in RENOMBRAR and RENOMBRAR[c] != c:
        c = RENOMBRAR[c]
    return c


def normal(s):
    """Compara valores sin diferencias de formato (espacios, 3008.0 frente a 3008, fechas)."""
    s = s.astype("string").str.strip()
    if s.dropna().str.match(r"^\d{4}-\d{2}-\d{2} \d").all() and s.notna().any():
        return pd.to_datetime(s, format="mixed").dt.strftime("%Y-%m-%d %H:%M:%S.%f").astype("string")
    num = pd.to_numeric(s, errors="coerce")
    return s.where(num.isna(), num.map(lambda v: f"{v:.3f}" if pd.notna(v) else pd.NA).astype("string"))


if __name__ == "__main__":
    filas = []
    for fuente, (limpia, kf, kl) in TABLAS.items():
        f = leer(fuente)
        l = pd.read_csv(LIMPIO / f"{limpia}.csv", dtype=str, na_values=[chr(92) + "N"], keep_default_na=False)
        if kf:
            f = f.drop_duplicates(kf)  # dt_officer trae 4 ids duplicados (fusionados)
            m = f.merge(l, left_on=kf, right_on=kl, how="left", suffixes=("", "__l"), indicator=True)
            perdidas = int((m["_merge"] != "both").sum())
        else:
            m = pd.concat([f.reset_index(drop=True), l.add_suffix("__l")], axis=1)
            perdidas = len(f) - len(l)
        for c in f.columns:
            if (fuente, c) in ELIMINADAS:
                filas.append(dict(tabla=fuente, columna=c, destino="(eliminada)", celdas_cambiadas="", nota="vacia o constante"))
                continue
            dest = EXTRA.get((fuente, c), final(c))
            col_l = dest if dest in l.columns and dest != c else dest
            nombre_m = col_l + "__l" if (col_l + "__l") in m.columns else col_l
            if nombre_m not in m.columns or (nombre_m == c and c not in l.columns):
                filas.append(dict(tabla=fuente, columna=c, destino="FALTA", celdas_cambiadas="", nota="no llego al modelo"))
                continue
            a, b = normal(m[c]), normal(m[nombre_m])
            ambos = a.notna() & b.notna()
            distintos = int(((a != b) & ambos).sum() + (a.isna() != b.isna()).sum())
            a_nulo = int((a.notna() & b.isna()).sum())
            originales = [x for x in l.columns if x.startswith(dest) and x.endswith(("_original", "_alternate"))]
            filas.append(dict(tabla=fuente, columna=c, destino=dest, celdas_cambiadas=distintos, pasan_a_nulo=a_nulo,
                              nota=("original en " + ", ".join(originales)) if originales and distintos else ""))
        filas.append(dict(tabla=fuente, columna="(filas)", destino=limpia, celdas_cambiadas=perdidas,
                          nota="filas de la fuente sin fila en el modelo"))
    out = pd.DataFrame(filas)
    with pd.option_context("display.width", 220, "display.max_rows", 300):
        print(out.to_string(index=False))
