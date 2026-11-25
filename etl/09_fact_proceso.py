"""Limpieza de fact_proceso (2.394.629 procesos) y tabla puente proceso-clasificacion.

Reglas acordadas (ninguna borra filas, todas marcan):
- oficial_id sin registro en dim_officer (5275) pasa a -1 "Desconocido"; original en oficial_id_origen.
- flag_canal_alternativo (servicio tipo 3), flag_festivo, flag_sin_atencion (completado sin estado
  En servicio o con atencion de 0 s), flag_cierre_lote (abandono cerrado en :00/:15/:30/:45),
  flag_cierre_otro_dia, flag_fuera_horario (llegada antes de las 7 o desde las 20).
- flag_dia_volumen_bajo y flag_dia_volumen_alto: z robusto < -3,5 o > 3,5 dentro de su dia de la
  semana. Separados porque un dia casi vacio (festivo) y un pico de demanda real no son lo mismo.
- flag_espera_atipica: espera > Q3 + 3 IQR calculado por tipo de servicio (sobre esperas > 0),
  porque caja y asesoria tienen distribuciones distintas. Las esperas largas se conservan.
- flag_atencion_corta: atencion mayor que 0 y menor que el umbral de "servicio corto" que Qflow configura en cada
  servicio (sst_threshold, 50 s en todos los servicios con atenciones), solo si el servicio tiene
  activada esa revision (check_short_service_time = 1). El PDF no fija ningun umbral.
  flag_atencion_larga (> 2 h).
- flag_con_transferencia: proceso con al menos una transferencia. Sirve para aislar el sesgo de
  flag_espera_sobre_estandar, que compara la espera de varias colas contra el estandar de una sola.
- Derivadas: fecha_llegada, hora_llegada, tiempo_no_explicado_seg (los negativos entre -1 y 0 s son
  redondeo, porque el total tiene milisegundos y los componentes segundos enteros, y se llevan a 0),
  flag_espera_sobre_estandar.
- espera_seg nula se deja nula (el proceso nunca paso por un estado de espera).
"""
import pandas as pd

from config import LIMPIO, guardar, leer

FESTIVOS = ["2017-08-07", "2017-08-21", "2017-10-16"]
Z_DIA_ATIPICO = 3.5
ATENCION_LARGA = 7200
HORA_APERTURA, HORA_CIERRE = 7, 19

if __name__ == "__main__":
    df = leer("fact_proceso")
    n_original = len(df)

    for c in ["espera_seg", "atencion_seg", "retenido_seg"]:
        v = pd.to_numeric(df[c])
        assert (v.dropna() % 1 == 0).all(), c
        df[c] = v.astype("Int64")
    for c in ["n_pasos", "n_llamados", "n_transferencias", "qnumber", "abandono", "resolution", "last_proc_status"]:
        df[c] = df[c].astype(int)
    df["tiempo_total_seg"] = pd.to_numeric(df["tiempo_total_seg"])

    llegada = pd.to_datetime(df["arrival_dt"], format="mixed")
    cierre = pd.to_datetime(df["last_update_dt"], format="mixed")
    df["arrival_dt"] = llegada.dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
    df["last_update_dt"] = cierre.dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
    df["fecha_llegada"] = llegada.dt.strftime("%Y-%m-%d")
    df["hora_llegada"] = llegada.dt.hour

    # oficial sin registro
    oficiales = set(pd.read_csv(LIMPIO / "dim_officer.csv", dtype=str)["officer_id"])
    df["oficial_id_origen"] = df["oficial_id"]
    sin_registro = df["oficial_id"].notna() & ~df["oficial_id"].isin(oficiales)
    df.loc[sin_registro, "oficial_id"] = "-1"

    servicios = pd.read_csv(LIMPIO / "dim_service.csv", dtype=str, na_values=[r"\N"], keep_default_na=False)
    assert df["service_id"].isin(set(servicios["service_id"])).all()
    assert df["last_service_id"].isin(set(servicios["service_id"])).all()
    srv = servicios.set_index("service_id")

    no_explicado = (df["tiempo_total_seg"] - df["espera_seg"].fillna(0)
                    - df["atencion_seg"].fillna(0) - df["retenido_seg"].fillna(0)).round(3)
    assert (no_explicado >= -1).all(), "hay negativos que no son redondeo"
    df["tiempo_no_explicado_seg"] = no_explicado.clip(lower=0)
    estandar = pd.to_numeric(df["service_id"].map(srv["waiting_time_standard"]))
    df["flag_espera_sobre_estandar"] = (df["espera_seg"] > estandar).astype("Int64").where(
        estandar.notna() & df["espera_seg"].notna())

    df["flag_canal_alternativo"] = df["service_id"].map(srv["is_alternative_channel"]).astype(int)
    df["flag_festivo"] = df["fecha_llegada"].isin(FESTIVOS).astype(int)
    df["flag_sin_atencion"] = ((df["resolution"] == 0)
                               & (df["atencion_seg"].isna() | (df["atencion_seg"] == 0))).astype(int)
    df["flag_cierre_lote"] = ((df["resolution"] == 3) & (cierre.dt.minute % 15 == 0)
                              & (cierre.dt.second < 5)).astype(int)
    df["flag_cierre_otro_dia"] = (cierre.dt.normalize() != llegada.dt.normalize()).astype(int)
    df["flag_fuera_horario"] = (~df["hora_llegada"].between(HORA_APERTURA, HORA_CIERRE)).astype(int)

    por_dia = df.groupby("fecha_llegada").size().to_frame("n")
    por_dia["dow"] = pd.to_datetime(por_dia.index).dayofweek
    mediana = por_dia.groupby("dow")["n"].transform("median")
    mad = por_dia.groupby("dow")["n"].transform(lambda s: (s - s.median()).abs().median())
    por_dia["z"] = 0.6745 * (por_dia["n"] - mediana) / mad
    dias_bajos = por_dia.index[por_dia["z"] < -Z_DIA_ATIPICO]
    dias_altos = por_dia.index[por_dia["z"] > Z_DIA_ATIPICO]
    dias_atipicos = dias_bajos.append(dias_altos)
    df["flag_dia_volumen_bajo"] = df["fecha_llegada"].isin(dias_bajos).astype(int)
    df["flag_dia_volumen_alto"] = df["fecha_llegada"].isin(dias_altos).astype(int)

    tipo = df["service_id"].map(srv["service_type_name"])
    esperas = df.loc[df["espera_seg"] > 0, "espera_seg"].astype(float)
    cuartiles = esperas.groupby(tipo).quantile([0.25, 0.75]).unstack()
    umbral_espera = cuartiles[0.75] + 3 * (cuartiles[0.75] - cuartiles[0.25])
    df["flag_espera_atipica"] = (df["espera_seg"] > tipo.map(umbral_espera)).fillna(False).astype(int)
    umbral_corto = pd.to_numeric(df["service_id"].map(srv["sst_threshold"]))
    revisa_corto = df["service_id"].map(srv["check_short_service_time"]) == "1"
    # mayor que 0: una atencion de 0 s no es atencion real y ya esta en flag_sin_atencion (las marcas son excluyentes)
    df["flag_atencion_corta"] = ((df["atencion_seg"] > 0) & (df["atencion_seg"] < umbral_corto)
                                 & revisa_corto).fillna(False).astype(int)
    df["flag_con_transferencia"] = (df["n_transferencias"] > 0).astype(int)
    df["flag_atencion_larga"] = (df["atencion_seg"] > ATENCION_LARGA).fillna(False).astype(int)

    assert df["process_id"].is_unique and len(df) == n_original
    guardar(df, "fact_proceso")

    puente = (df.loc[df["clasificaciones"].notna(), ["process_id", "clasificaciones"]]
              .assign(classification_id=lambda d: d["clasificaciones"].str.split())
              .explode("classification_id")[["process_id", "classification_id"]]
              .drop_duplicates())
    clasif = set(pd.read_csv(LIMPIO / "dim_classification.csv", dtype=str)["classification_id"])
    assert puente["classification_id"].isin(clasif).all()
    guardar(puente, "puente_proceso_clasificacion")

    print(f"filas {len(df):,} | oficial -> -1: {sin_registro.sum()} | negativos llevados a 0: {(no_explicado < 0).sum():,}")
    print("umbral espera atipica por tipo (s):", umbral_espera.round(0).to_dict())
    print("dias atipicos:", por_dia.loc[dias_atipicos, ["n", "z"]].round(1).to_dict("index"))
    flags = [c for c in df.columns if c.startswith("flag_")]
    resumen = pd.DataFrame({"filas": df[flags].sum(), "%": (100 * df[flags].sum() / len(df)).round(2)})
    print(resumen.to_string())
    print(f"puente: {len(puente):,} filas, {puente.process_id.nunique():,} procesos")
