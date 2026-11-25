"""Limpieza de dt_classification (75 filas, 73 ids).

Reglas acordadas:
- Ids 145 y 146 vienen en dos grupos (5 Ahorros y Cuenta Corriente, 16 Servicio Posventa) y el
  proceso no dice cual aplica: una fila por id con el grupo combinado y multigrupo = 1.
  La columna se llama classification_group_ids (texto, "5/16") porque es una lista de grupos y no un id
  entero como classification_group_id de dim_service.
- Grupo nulo pasa a "Sin identificar" (21 clasificaciones del catalogo anterior, ninguna con procesos).
- Dobles espacios a uno, tildes perdidas y erratas ("Virutal", "desbloque", "enel"). Los nombres
  cortados en 50 caracteres y las abreviaturas del origen no se pueden reconstruir.
"""
from config import SIN_IDENTIFICAR, guardar, leer


def palabra(p):
    """Regex que encuentra p como palabra completa."""
    return f"(?<![A-Za-z]){p}(?![A-Za-z])"


# Tildes y erratas (revision critica)
CORRECCIONES = {palabra("Atencion"): "Atención", palabra("Actualizacion"): "Actualización",
                palabra("Republica"): "República", palabra("debito"): "débito",
                palabra("desbloque"): "desbloqueo", palabra("enel"): "en el",
                palabra("FIDUCIA"): "Fiducia", palabra("Virutal"): "Virtual",
                # mayusculas a mitad de nombre (solo despues de un espacio, no la primera palabra)
                "(?<= )" + palabra("Producto"): "producto", "(?<= )" + palabra("Productos"): "productos",
                "(?<= )" + palabra("Chequeras"): "chequeras", "(?<= )" + palabra("Novedades"): "novedades",
                "(?<= )" + palabra("Comerciales"): "comerciales",
                "Créditos hipotecario": "Crédito Hipotecario"}

if __name__ == "__main__":
    df = leer("dt_classification")
    n_original = len(df)
    df["classification_name"] = (df["classification_name"].str.replace(r"\s+", " ", regex=True).str.strip()
                                 .replace(CORRECCIONES, regex=True))
    df["groupname"] = df["groupname"].fillna(SIN_IDENTIFICAR)
    df = (df.groupby("classification_id", sort=False)
            .agg(classification_name=("classification_name", "first"),
                 classification_group_ids=("classificationgroup_id", lambda s: "/".join(s.dropna()) or None),
                 groupname=("groupname", " / ".join),
                 parentgroup_id=("parentgroup_id", "first"),
                 multigrupo=("groupname", lambda s: int(len(s) > 1)))
            .reset_index())
    assert df["classification_id"].is_unique
    guardar(df, "dim_classification")
    print(f"filas originales {n_original}, salida {len(df)}")
    print(df[df.multigrupo == 1].to_string(index=False))
