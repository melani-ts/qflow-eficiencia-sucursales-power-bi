"""Limpieza de dt_officer (10.483 filas, 10.479 ids).

Reglas acordadas:
- 4 ids duplicados (1298, 1616, 1817, 2479, sin procesos): se conserva la contratacion mas
  antigua y la otra fecha queda en hire_date_alterna.
- hire_date 0 y posteriores al periodo de datos (2017-10-31) pasan a nulo con flag_hire_date_invalida.
- location_name: "Recepción1" se unifica con "Recepción 1". groupname nulo pasa a "Sin identificar",
  tilde en "Dirección General", "Administrators" traducido a "Administradores" y "MATEO" (nombre de
  persona, no un cargo) pasa a "Sin identificar".
- group_category: familia funcional del grupo (Caja, Asesoria, Direccion, ...).
- Fila -1 "Sin identificar" para oficial_id de fact_proceso que no existe en dt_officer (5275).
"""
import pandas as pd

from config import SIN_IDENTIFICAR, guardar, leer

FIN_DATOS = pd.Timestamp("2017-10-31")
# "MATEO" es un nombre de persona y no un grupo o cargo (220 oficiales, ninguno con procesos)
GRUPOS = {"Direccion General": "Dirección General", "Administrators": "Administradores",
          "MATEO": SIN_IDENTIFICAR}
# Familia funcional del grupo, segun lo que atiende en los procesos (porcentaje de caja y asesoria,
# duracion de la atencion) y su puesto. Supernumerarios atiende 84 % caja (reemplazo de cajeros);
# Supernumerarios de Director atiende 76 % asesoria con atencion como la de los directores.
CATEGORIA_GRUPO = {
    "Cajeros": "Caja", "Cajeros Principales": "Caja", "Supernumerarios": "Caja",
    "Asesores Comerciales": "Asesoría", "Asesor MiPYME": "Asesoría", "Ejecutivos": "Asesoría",
    "Directores/Gerentes": "Dirección", "Dirección General": "Dirección",
    "Supernumerarios de Director": "Dirección",
    "Redireccionadores": "Redirección", "Coordinadores de Horario Extendido": "Coordinación",
    "Administradores": "Administración del sistema", "Administrador de Contenidos": "Administración del sistema",
    "Gestión de Usuarios": "Administración del sistema", "Monitoreo Equipo Tactic": "Administración del sistema",
    "Corresponsales Bancarios": "Corresponsales Bancarios", "Ayudantes de Proceso": "Ayudantes de Proceso",
    "GR y LR de Servicio": "GR y LR de Servicio", SIN_IDENTIFICAR: SIN_IDENTIFICAR,
}

if __name__ == "__main__":
    df = leer("dt_officer")
    n_original = len(df)
    fecha = pd.to_datetime(df["hire_date"], format="%Y%m%d", errors="coerce")
    invalida = df["hire_date"].notna() & (fecha.isna() | (fecha > FIN_DATOS))
    df["flag_hire_date_invalida"] = invalida.astype(int)
    df["hire_date"] = fecha.where(~invalida)

    df = df.sort_values(["officer_id", "hire_date"])
    df["hire_date_alterna"] = df.groupby("officer_id")["hire_date"].transform("last")
    df.loc[df["hire_date_alterna"] == df["hire_date"], "hire_date_alterna"] = pd.NaT
    df = df.drop_duplicates("officer_id", keep="first")

    df["location_name"] = df["location_name"].str.strip().replace({"Recepción1": "Recepción 1"})
    df["group_name_original"] = df["groupname"]  # conserva "MATEO" y el vacio del origen
    df["groupname"] = df["groupname"].fillna(SIN_IDENTIFICAR).replace(GRUPOS)
    df["es_placeholder"] = 0

    fp = leer("fact_proceso", usecols=["oficial_id"])
    faltan = sorted(set(fp["oficial_id"].dropna()) - set(df["officer_id"]), key=int)
    desconocido = pd.DataFrame([{"officer_id": "-1", "location_name": None, "groupname": SIN_IDENTIFICAR,
                                 "hire_date": pd.NaT, "flag_hire_date_invalida": 0,
                                 "hire_date_alterna": pd.NaT, "es_placeholder": 1}])
    df = pd.concat([df, desconocido], ignore_index=True)
    faltan_categoria = set(df["groupname"]) - set(CATEGORIA_GRUPO)
    assert not faltan_categoria, f"grupos sin categoria: {faltan_categoria}"
    df["group_category"] = df["groupname"].map(CATEGORIA_GRUPO)
    df = df.sort_values("officer_id", key=lambda s: s.astype(int))
    for c in ["hire_date", "hire_date_alterna"]:
        df[c] = pd.to_datetime(df[c]).dt.strftime("%Y-%m-%d")

    assert df["officer_id"].is_unique
    guardar(df, "dim_officer")
    print(f"filas originales {n_original}, salida {len(df)} (4 duplicados fusionados, +1 fila -1 Sin identificar)")
    print("ids de fact_proceso sin oficial (van a -1):", faltan)
    print("fechas invalidas:", int(invalida.sum()))
    print(df[df.hire_date_alterna.notna()].to_string(index=False))
