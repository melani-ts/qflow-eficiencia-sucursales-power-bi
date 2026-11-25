"""Limpieza de los 12 diccionarios dic_*.

Reglas acordadas (ver bitacora_limpieza.md, seccion Diccionarios):
- Decodificar latin-1 a UTF-8 y reconstruir dic_signoutreason_id (fin de linea CR), en config.leer.
- Quitar espacios sobrantes en encabezados y textos, corregir erratas y tildes.
- Renombrar la clave al nombre de la columna que la usa en las tablas.
- Codigos duplicados: se conservan todos y se agrega 'categoria' (opcion A).
- Subniveles 5-7 (Micropyme) y 9-11 (Pyme): etiqueta unica con el segmento y 'categoria' = tamano.
- Segmentos 19 y 20: categoria comun 'Sin segmento'.
- Estados del oficial agrupados por capacidad (0 fuera de servicio, 1-2 libre, 3-5 atendiendo, 4 trastienda, 6 recepcion).
- Codigos usados en las tablas pero ausentes del diccionario: fila 'Codigo X (sin descripcion)'
  con en_diccionario_original = 0.
"""
import pandas as pd

from config import SIN_IDENTIFICAR, guardar, leer

# Ortografia: tildes perdidas y erratas del original
CORRECCIONES = {
    "univesitario": "Universitario", "Unknonw": "Unknown", "Esperando union": "Esperando unión",
    "PEQUENO": "Pequeño", "PEQUENA": "Pequeño", "MEDIANO": "Mediano", "MEDIANA": "Mediano",
    "BASICO": "Básico", "ENTES AUTONOMOS": "Entes autónomos", "ORGANOS DE CONTROL": "Órganos de control",
    "Gestion Comercial": "Gestión comercial", "union libre": "Unión libre",
    "INTERNACIONAL": "Internacional", "MI NEGOCIO": "Mi negocio",
}
# Correcciones sobre el texto ya formateado (revision critica)
CORRECCIONES_FINALES = {
    "Esperar union": "Esperar unión", "No Aplica": "No aplica", "Vip": "VIP",
    "Gestión Comercial / Sistematica": "Gestión comercial / Sistemática",
}

# (archivo original, archivo limpio, clave original, clave nueva, columna descripcion, otras columnas)
DICCIONARIOS = [
    ("dic_action", "dic_action", "action", "action", "desc_espanol", ["desc_ingles", "mnemonico"]),
    ("dic_backofficetask_id", "dic_backofficetask", "backofficetask_id", "backofficetask_id", "taskname", []),
    ("dic_customer_level_id", "dic_customer_level", "customerlevel_id", "customer_level_id", "customerlevelname", []),
    ("dic_education_level", "dic_education_level", "education_level", "education_level", "desc_education_level", []),
    ("dic_housing_type", "dic_housing_type", "housing_type", "housing_type", "desc_housing_type", []),
    ("dic_marital_status", "dic_marital_status", "marital_state", "marital_state", "desc_marital_state", []),
    ("dic_occupation_cod", "dic_occupation", "occupation_cod", "occupation_cod", "desc_occupation", []),
    ("dic_officer_status_id", "dic_officer_status", "officer_status_id", "officer_status_id", "desc_espanol", ["desc_ingles"]),
    ("dic_proc_status_id", "dic_proc_status", "proc_status_id", "proc_status_id", "desc_espanol", ["desc_ingles", "mnemonico", "esperando"]),
    ("dic_resolution", "dic_resolution", "resolution", "resolution", "desc_espanol", ["desc_ingles"]),
    ("dic_signoutreason_id", "dic_signoutreason", "signoutreason_id", "signoutreason_id", "reasonname", []),
    ("dic_sublevel_id", "dic_sublevel", "sub_level_cod", "sublevel_id", "desc_sublevel", []),
]

SUBNIVEL_ETIQUETA = {
    "5": ("Pequeño (Micropyme)", "Pequeño"), "6": ("Mediano (Micropyme)", "Mediano"),
    "7": ("Grande (Micropyme)", "Grande"), "9": ("Pequeño (Pyme)", "Pequeño"),
    "10": ("Mediano (Pyme)", "Mediano"), "11": ("Grande (Pyme)", "Grande"),
}

# Categorias que agrupan codigos de la misma familia (revision de dimensiones)
CATEGORIA_OCUPACION = {"Desempleado con ingresos": "Desempleado", "Desempleado sin ingresos": "Desempleado",
                       "Profesional independiente": "Independiente"}
SEGMENTO_BASE = {"Constructor corporativo": "Corporativo", "Constructor empresarial": "Empresarial",
                 "Constructor pyme": "Pyme", "Gobierno de red": "Gobierno"}
CATEGORIA_SUBNIVEL = {"Valor alto": "Alto", "Valor medio": "Medio", "Valor bajo": "Bajo"}

CATEGORIA_ESTADO_OFICIAL = {"0": "Fuera de servicio", "1": "Capacidad libre", "2": "Capacidad libre",
                            "3": "Atendiendo", "4": "Trastienda", "5": "Atendiendo", "6": "Recepción"}

# Columnas de las tablas de datos que usan cada diccionario (para detectar codigos sin descripcion)
USOS = {
    "dic_customer_level": [("dt_customer", "customer_level_id")],
    "dic_sublevel": [("dt_customer", "sublevel_id")],
    "dic_occupation": [("dt_customer", "occupation_cod")],
    "dic_marital_status": [("dt_customer", "marital_state")],
    "dic_housing_type": [("dt_customer", "housing_type")],
    "dic_education_level": [("dt_customer", "education_level")],
    "dic_officer_status": [("fact_oficial_hora", "officer_status_id")],
    "dic_proc_status": [("fact_proceso", "last_proc_status")],
    "dic_resolution": [("fact_proceso", "resolution")],
}


def texto(s):
    """Recorta espacios, corrige ortografia y pasa a mayuscula inicial."""
    s = s.str.strip()
    s = s.map(lambda v: CORRECCIONES.get(v, v) if isinstance(v, str) else v)
    s = s.map(lambda v: v[0].upper() + v[1:].lower() if isinstance(v, str) and v.isupper() else
              (v[0].upper() + v[1:] if isinstance(v, str) and v else v))
    return s.map(lambda v: CORRECCIONES_FINALES.get(v, v) if isinstance(v, str) else v)


_cache = {}


def codigos_usados(tabla, columna):
    if (tabla, columna) not in _cache:
        df = leer(tabla, usecols=[columna])
        _cache[(tabla, columna)] = set(df[columna].dropna().str.strip()) - {""}
    return _cache[(tabla, columna)]


def limpiar(origen, destino, clave, clave_nueva, col_desc, otras):
    df = leer(origen)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Mnemonico": "mnemonico"})
    out = pd.DataFrame({clave_nueva: df[clave].str.strip(), "descripcion": texto(df[col_desc])})
    for c in otras:
        out[c] = df[c].str.strip() if c == "mnemonico" or c == "esperando" else texto(df[c])
    out["categoria"] = out["descripcion"]

    if destino == "dic_sublevel":
        for cod, (etiqueta, tamano) in SUBNIVEL_ETIQUETA.items():
            m = out[clave_nueva] == cod
            out.loc[m, "descripcion"] = etiqueta
            out.loc[m, "categoria"] = tamano
    if destino == "dic_customer_level":
        out.loc[out[clave_nueva].isin(["19", "20"]), "categoria"] = SIN_IDENTIFICAR
        # variantes de un segmento base: sector construccion y gobierno de red
        out["categoria"] = out["categoria"].replace(SEGMENTO_BASE)
    if destino == "dic_marital_status":
        out.loc[out[clave_nueva] == "I", "categoria"] = SIN_IDENTIFICAR  # "No informa"
    if destino == "dic_proc_status":
        # mayuscula inicial: "Esperado y Abortado" y "Servido y abortado" quedan con el mismo formato
        out["descripcion"] = out["descripcion"].map(lambda v: v[0] + v[1:].lower())
        out["categoria"] = out["descripcion"]
        out.loc[out[clave_nueva] == "99", ["descripcion", "categoria"]] = SIN_IDENTIFICAR  # "Desconocido"
    if destino == "dic_occupation":
        out["categoria"] = out["categoria"].replace(CATEGORIA_OCUPACION)
    if destino == "dic_sublevel":
        out["categoria"] = out["categoria"].replace(CATEGORIA_SUBNIVEL)
    if destino == "dic_officer_status":
        out["categoria"] = out[clave_nueva].map(CATEGORIA_ESTADO_OFICIAL)
    out["en_diccionario_original"] = 1

    faltantes = set()
    for tabla, col in USOS.get(destino, []):
        faltantes |= codigos_usados(tabla, col) - set(out[clave_nueva])
    if faltantes:
        orden = sorted(faltantes, key=lambda v: (not v.isdigit(), int(v) if v.isdigit() else 0, v))
        extra = pd.DataFrame({clave_nueva: orden,
                              "descripcion": [f"Código {v} (sin descripción)" for v in orden],
                              "en_diccionario_original": 0})
        extra["categoria"] = extra["descripcion"]  # codigos distintos no se juntan en una sola categoria
        out = pd.concat([out, extra], ignore_index=True)

    assert out[clave_nueva].is_unique, f"clave duplicada en {destino}"
    guardar(out, destino)
    print(f"{destino:22s} filas originales {len(df):3d}  agregadas sin descripcion {len(faltantes):2d}"
          f"  {sorted(faltantes) if faltantes else ''}")
    return out


if __name__ == "__main__":
    for args in DICCIONARIOS:
        limpiar(*args)
