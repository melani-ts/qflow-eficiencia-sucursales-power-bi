"""Limpieza de fact_oficial_hora (176.764 filas).

Reglas acordadas:
- Cada evento se asigna a la hora en que empezo, por lo que seg puede superar el maximo fisico de
  la hora (n_oficiales x 3.600). Se conserva seg, se marca flag_excede_hora y se agrega
  seg_tope_hora = min(seg, n_oficiales x 3.600).
- Horas fuera de atencion (antes de las 7 o desde las 20) se marcan con flag_fuera_horario.
"""
import pandas as pd

from config import guardar, leer

HORA_APERTURA, HORA_CIERRE = 7, 19

if __name__ == "__main__":
    df = leer("fact_oficial_hora")
    n_original = len(df)
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")
    for c in ["hora", "n_eventos", "n_oficiales"]:
        df[c] = df[c].astype(int)
    df["seg"] = df["seg"].astype(float).astype("int64")  # todos los valores son enteros
    tope = df["n_oficiales"] * 3600
    df["flag_excede_hora"] = (df["seg"] > tope).astype(int)
    df["seg_tope_hora"] = df["seg"].clip(upper=tope)
    df["flag_fuera_horario"] = (~df["hora"].between(HORA_APERTURA, HORA_CIERRE)).astype(int)

    assert not df.duplicated(["fecha", "hora", "qf_branch_id", "officer_status_id"]).any()
    assert len(df) == n_original
    guardar(df, "fact_oficial_hora")
    print(f"filas {len(df)}, excede hora {df.flag_excede_hora.sum()}, fuera de horario {df.flag_fuera_horario.sum()}")
    print(f"suma seg {df.seg.sum():,} | suma seg_tope_hora {df.seg_tope_hora.sum():,}")
    print(df.groupby("officer_status_id")[["seg", "seg_tope_hora"]].sum().to_string())
