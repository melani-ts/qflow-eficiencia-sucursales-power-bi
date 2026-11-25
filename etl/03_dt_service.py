"""Limpieza de dt_service (1.087 servicios).

Reglas acordadas:
- Unificar servicename a la grafia con tildes (texto original en servicename_original). Misma regla
  para profilename y attributename. servicetypename con mayuscula inicial. Los placeholders usan "Sin identificar" en nombre y tipo.
- Quitar customerpatience (100 % vacia), maxlockduration y oncallagainmessagetype (constantes).
- Marcar canales alternativos (servicetype_id 3) con es_canal_alternativo.
- Incorporar los 6 last_service_id de fact_proceso que no estan en dt_service. Solo existen en
  dt_function_l; su sucursal se infiere por dt_function_s y queda en qf_branch_id_inferida,
  con qf_branch_id nulo porque esas sucursales no estan en dt_branch.
- waitingtimestandard y demas umbrales estan en segundos (540 a 2.700 s frente a una mediana
  real de espera de 969 s en caja y 1.359 s en asesoria).
"""
import pandas as pd

from config import SIN_IDENTIFICAR, guardar, leer

GRAFIAS = {"Asesoria Basica": "Asesoría Básica", "Asesoria General": "Asesoría General",
           "Asesoria Preferencial": "Asesoría Preferencial", "Asesoria Prioritaria": "Asesoría Prioritaria",
           "Asesoria Pyme": "Asesoría Pyme", "Asesoria Virtual": "Asesoría Virtual"}
# Misma regla de tildes para perfil y atributo (revision critica)
PALABRAS_TILDE = {"(?<![A-Za-z])Asesoria(?![A-Za-z])": "Asesoría", "(?<![A-Za-z])Basica(?![A-Za-z])": "Básica",
                  "ServicioEspecial": "Servicio Especial"}
TIPO_SERVICIO = {"CAJA": "Caja", "ASESORÍA": "Asesoría", "CANALES ALTERNATIVOS": "Canales alternativos"}
QUITAR = ["customerpatience", "maxlockduration", "oncallagainmessagetype"]

if __name__ == "__main__":
    df = leer("dt_service")
    n_original = len(df)
    for c in QUITAR:
        assert df[c].nunique() <= 1, f"{c} ya no es constante"
    df = df.drop(columns=QUITAR)
    df["servicename_original"] = df["servicename"]
    df["servicename"] = df["servicename"].str.strip().replace(GRAFIAS)
    for c in ["profilename", "attributename"]:
        df[c] = df[c].str.strip().replace(PALABRAS_TILDE, regex=True)
    assert df["servicetypename"].isin(TIPO_SERVICIO).all()
    df["servicetypename"] = df["servicetypename"].map(TIPO_SERVICIO)
    df["es_canal_alternativo"] = (df["servicetype_id"] == "3").astype(int)
    df["es_placeholder"] = 0
    df["qf_branch_id_inferida"] = pd.NA

    # servicios usados en fact_proceso que faltan en dt_service
    fp = leer("fact_proceso", usecols=["service_id", "last_service_id"])
    usados = set(fp["service_id"]) | set(fp["last_service_id"])
    faltan = sorted(usados - set(df["service_id"]), key=int)
    fl, fs = leer("dt_function_l"), leer("dt_function_s")
    sucursal = (fl[fl["service_id"].isin(faltan)].merge(fs, on="function_id")
                .groupby("service_id")["qf_branch_id"].agg(lambda s: "/".join(sorted(set(s)))))
    assert not sucursal.str.contains("/").any(), "un servicio no catalogado aparece en mas de una sucursal"
    extra = pd.DataFrame({"service_id": faltan, "servicename": SIN_IDENTIFICAR,
                          "servicetypename": SIN_IDENTIFICAR,
                          "servicename_original": pd.NA, "es_canal_alternativo": 0, "es_placeholder": 1,
                          "qf_branch_id": pd.NA, "qf_branch_id_inferida": [sucursal.get(s, pd.NA) for s in faltan]})
    df = pd.concat([df, extra], ignore_index=True)
    df["qf_branch_id_inferida"] = df["qf_branch_id_inferida"].astype("Int64")  # una sola sucursal por servicio

    assert df["service_id"].is_unique
    guardar(df, "dim_service")
    print(f"filas originales {n_original}, agregadas {len(extra)}, total {len(df)}")
    print(extra[["service_id", "qf_branch_id_inferida"]].to_string(index=False))
    print(df.groupby(["servicetypename", "servicename"], dropna=False).size().to_string())
