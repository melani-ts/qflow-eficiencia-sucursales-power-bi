"""Limpieza de dt_customer (776.980 clientes).

Reglas acordadas:
- birth_year valido entre 1923 y 2019. Fuera de ese rango (rellenos 0, 1900, 1910 y 1920 con el
  ruido de +-2 del anonimato, y anios imposibles) pasa a nulo con flag_birth_year_invalido. Original en birth_year_original.
- rango_edad de 10 anios calculado a 2017 (no edad exacta, por el ruido de +-2).
- occupation_cod " " pasa a nulo.
- registered_svp y registered_app: nulo se conserva como "sin informacion".
- Los codigos se mantienen; los que no tenian descripcion ya estan en los diccionarios limpios.
- Atributos legibles de los diccionarios integrados en la dimension (segment_name, sublevel_name,
  education_level_name, etc.), como pide el PDF para el esquema en estrella.
"""
import pandas as pd

from config import LIMPIO, SIN_IDENTIFICAR, guardar, leer

ANIO_MIN, ANIO_MAX, ANIO_REF = 1923, 2019, 2017
BANDAS = [(-99, 17, "<18"), (18, 29, "18-29"), (30, 39, "30-39"), (40, 49, "40-49"),
          (50, 59, "50-59"), (60, 69, "60-69"), (70, 200, "70+")]
DICS = {"customer_level_id": "dic_customer_level", "sublevel_id": "dic_sublevel",
        "occupation_cod": "dic_occupation", "marital_state": "dic_marital_status",
        "housing_type": "dic_housing_type", "education_level": "dic_education_level"}
# columna legible: (codigo, campo del diccionario limpio)
LEGIBLES = {"segment_name": ("customer_level_id", "description"),
            "segment_category": ("customer_level_id", "category"),
            "sublevel_name": ("sublevel_id", "description"),
            "sublevel_category": ("sublevel_id", "category"),
            "occupation_name": ("occupation_cod", "description"),
            "occupation_category": ("occupation_cod", "category"),
            "marital_status_name": ("marital_state", "category"),
            "housing_type_name": ("housing_type", "category"),
            "education_level_name": ("education_level", "category")}


def banda(edad):
    if pd.isna(edad):
        return SIN_IDENTIFICAR
    return next(etq for lo, hi, etq in BANDAS if lo <= edad <= hi)


if __name__ == "__main__":
    df = leer("dt_customer")
    n_original = len(df)
    for c in df.columns:
        df[c] = df[c].str.strip().replace("", pd.NA)

    anio = pd.to_numeric(df["birth_year"])
    invalido = anio.notna() & ~anio.between(ANIO_MIN, ANIO_MAX)
    df["birth_year_original"] = df["birth_year"]
    df["birth_year"] = anio.where(~invalido).astype("Int64")
    df["flag_birth_year_invalido"] = invalido.astype(int)
    df["rango_edad"] = (ANIO_REF - df["birth_year"]).map(banda)

    diccionarios = {}
    for col, dic in DICS.items():
        diccionarios[col] = pd.read_csv(LIMPIO / f"{dic}.csv", dtype=str).set_index(col)
        fuera = set(df[col].dropna()) - set(diccionarios[col].index)
        assert not fuera, f"{col}: codigos sin diccionario {fuera}"

    # Atributos legibles integrados en la dimension (el PDF pide que los diccionarios se integren como
    # atributos de las dimensiones). En los codigos duplicados (H/B, C/M...) se usa la categoria unificada.
    # El cliente sin codigo queda como "Sin identificar", igual que age_range.
    # Si el codigo no tenia descripcion se usa "Codigo X (sin descripcion)" para no juntar codigos distintos.
    for nueva, (col, campo) in LEGIBLES.items():
        d = diccionarios[col]
        etiqueta = d[campo].where(d["in_original_dictionary"] == "1", d["description"])
        etiqueta = etiqueta.where(d["category"] != SIN_IDENTIFICAR, SIN_IDENTIFICAR)  # "Sin segmento", "No informa"
        df[nueva] = df[col].map(etiqueta).fillna(SIN_IDENTIFICAR)

    assert df["customer_id"].is_unique and len(df) == n_original
    guardar(df, "dim_customer")
    print(f"filas {len(df)}, birth_year invalidos {invalido.sum()} ({invalido.mean():.1%}), "
          f"nulos originales {anio.isna().sum()}, occupation nulo {df.occupation_cod.isna().sum()}")
    print(df["rango_edad"].value_counts().to_string())
