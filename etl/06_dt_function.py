"""Limpieza de dt_function_s (8.879) y dt_function_l (32.505).

Reglas acordadas: se carga toda la red (478 sucursales) con en_estudio = 1 cuando la sucursal
esta entre las 56 de dt_branch. Se recortan los espacios de prio_services y se pasa a mayusculas
(habia variantes como "EjecPyme" y "EJECPYME").
"""
from config import guardar, leer

if __name__ == "__main__":
    sucursales = set(leer("dt_branch")["qf_branch_id"])
    servicios = set(leer("dt_service")["service_id"])

    fs = leer("dt_function_s")
    fs["prio_services"] = fs["prio_services"].str.strip().str.upper()
    fs["en_estudio"] = fs["qf_branch_id"].isin(sucursales).astype(int)
    assert fs["function_id"].is_unique

    fl = leer("dt_function_l")
    fl["en_estudio"] = fl["function_id"].isin(set(fs.loc[fs.en_estudio == 1, "function_id"])).astype(int)
    fl["servicio_en_dim_service"] = fl["service_id"].isin(servicios).astype(int)
    assert not fl.duplicated(["function_id", "service_id"]).any()
    assert fl["function_id"].isin(set(fs["function_id"])).all()

    guardar(fs, "dim_function_s")
    guardar(fl, "dim_function_l")
    print(f"function_s {len(fs)} filas, en estudio {fs.en_estudio.sum()}")
    print(f"function_l {len(fl)} filas, en estudio {fl.en_estudio.sum()}, con servicio en dim_service {fl.servicio_en_dim_service.sum()}")
