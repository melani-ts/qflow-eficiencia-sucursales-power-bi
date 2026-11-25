"""Limpieza de dt_branch (56 sucursales).

Reglas acordadas: recortar espacios, quitar el prefijo ZONA, reparar NARI#O (Ñ dañada por
codificacion), corregir la errata BGOTA, restaurar tildes y dejar mayuscula inicial por palabra.
atiende_sabado: 1 si la sucursal tuvo llegadas en al menos la mitad de los sabados (33 sucursales;
atienden 12 o 13 de los 13 sabados, y las otras 23 ninguno).
"""
import pandas as pd

from config import guardar, leer

PALABRAS = {"NARI#O": "Nariño", "BGOTA": "Bogotá", "BOGOTA": "Bogotá", "BOYACA": "Boyacá",
            "ATLANTICO": "Atlántico", "SINU": "Sinú", "CUCUTA": "Cúcuta"}
MINUSCULAS = {"Y", "DE"}
# Region: agrupacion geografica de las 26 zonas (propia del analisis, no viene en la fuente)
REGION = {
    "Antioquia": ["Centro Antioquia", "Metropolitana Antioquia", "Occidente Antioquia", "Poblado Antioquia"],
    "Valle del Cauca": ["Cali Comercial", "Cali Pyme Preferencial", "Valle"],
    "Santanderes": ["Bucaramanga", "Santander y Cúcuta", "Norte de Santander y Arauca"],
    "Caribe": ["Atlántico", "Barranquilla", "Cartagena", "Sierra Nevada", "Sinú y Sabanas"],
}


def zona_legible(v):
    palabras = v.strip().split()
    if palabras and palabras[0] == "ZONA":
        palabras = palabras[1:]
    return " ".join(PALABRAS.get(p, p.lower() if p in MINUSCULAS else p.capitalize()) for p in palabras)


if __name__ == "__main__":
    df = leer("dt_branch")
    df["qf_branch_type"] = df["qf_branch_type"].str.strip()
    df["nombre_zona_original"] = df["nombre_zona"].str.rstrip()
    df["nombre_zona"] = df["nombre_zona"].map(zona_legible)
    zona_region = {z: r for r, zonas in REGION.items() for z in zonas}
    df["region"] = df["nombre_zona"].map(
        lambda z: "Bogotá y Sabana" if z.endswith("Bogotá y Sabana") else zona_region.get(z, z))

    # atiende sabado: la sucursal tuvo llegadas en al menos la mitad de los sabados del periodo
    fp = leer("fact_proceso", usecols=["arrival_dt", "qf_branch_id"])
    llegada = pd.to_datetime(fp["arrival_dt"], format="mixed")
    sabados = fp.loc[llegada.dt.dayofweek == 5].assign(dia=llegada.dt.date)
    total_sabados = sabados["dia"].nunique()
    sabados_abiertos = sabados.groupby("qf_branch_id")["dia"].nunique()
    df["atiende_sabado"] = (df["qf_branch_id"].map(sabados_abiertos).fillna(0) >= total_sabados / 2).astype(int)

    assert df["qf_branch_id"].is_unique
    guardar(df, "dim_branch")
    print(len(df), "filas")
    print(df.drop_duplicates("nombre_zona")[["nombre_zona_original", "nombre_zona"]].to_string(index=False))
