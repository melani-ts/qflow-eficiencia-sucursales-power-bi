"""Dimensiones de fecha (1 ago a 31 oct 2017) y hora (0 a 23).

Dia de pago: 15 y ultimo dia del mes (quincenas de nomina en Colombia); si cae en sabado,
domingo o festivo se adelanta al dia habil anterior (30 sep sabado pasa al 29, 15 oct domingo pasa al 13).
Dia habil: lunes a viernes sin festivos (en los bancos no se trabaja sabado ni domingo).
Dia de atencion: lunes a sabado sin festivos, porque las sucursales atienden el sabado en jornada
parcial (33 de 56 sucursales, sobre todo de 9 a 12). tipo_dia: Dia habil, Sabado (jornada parcial),
Domingo o Festivo.
Festivos de Colombia en el periodo: 7 ago (Batalla de Boyaca), 21 ago (Asuncion, trasladado)
y 16 oct (Dia de la Raza, trasladado).
"""
import pandas as pd

from config import guardar

FESTIVOS = {"2017-08-07": "Batalla de Boyacá", "2017-08-21": "Asunción de la Virgen",
            "2017-10-16": "Día de la Raza"}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = {8: "Agosto", 9: "Septiembre", 10: "Octubre"}


def franja(h):
    if 7 <= h <= 11:
        return "Mañana (7-11)"
    if 12 <= h <= 13:
        return "Mediodía (12-13)"
    if 14 <= h <= 17:
        return "Tarde (14-17)"
    if 18 <= h <= 19:
        return "Cierre (18-19)"
    return "Fuera de horario"


if __name__ == "__main__":
    f = pd.DataFrame({"fecha": pd.date_range("2017-08-01", "2017-10-31")})
    f["anio"] = f.fecha.dt.year
    f["mes"] = f.fecha.dt.month
    f["nombre_mes"] = f.mes.map(MESES)
    f["anio_mes"] = f.fecha.dt.strftime("%Y-%m")
    f["semana_iso"] = f.fecha.dt.isocalendar().week.astype(int)
    f["dia"] = f.fecha.dt.day
    f["dia_semana_num"] = f.fecha.dt.dayofweek + 1
    f["dia_semana"] = f.fecha.dt.dayofweek.map(dict(enumerate(DIAS)))
    f["quincena"] = (f.dia > 15).astype(int) + 1
    f["es_fin_de_semana"] = (f.dia_semana_num >= 6).astype(int)
    clave = f.fecha.dt.strftime("%Y-%m-%d")
    f["es_festivo"] = clave.isin(FESTIVOS).astype(int)
    # dia de pago: 15 y ultimo del mes; si cae en sabado, domingo o festivo se adelanta al dia habil anterior
    no_habil = (f.dia_semana_num >= 6) | (f.es_festivo == 1)
    pago = []
    for objetivo in f.loc[(f.dia == 15) | f.fecha.dt.is_month_end, "fecha"]:
        if no_habil[f.fecha == objetivo].iloc[0]:
            objetivo -= pd.Timedelta(days=1)
            while objetivo.dayofweek >= 5 or objetivo.strftime("%Y-%m-%d") in FESTIVOS:
                objetivo -= pd.Timedelta(days=1)
        pago.append(objetivo)
    f["es_dia_pago"] = f.fecha.isin(pago).astype(int)
    f["nombre_festivo"] = clave.map(FESTIVOS)
    # dia habil bancario: lunes a viernes sin festivos (en los bancos no se trabaja sabado ni domingo)
    f["es_dia_habil"] = ((f.dia_semana_num <= 5) & (f.es_festivo == 0)).astype(int)
    # las sucursales si atienden el sabado (jornada parcial en 33 de 56): dia de atencion = lunes a sabado sin festivos
    f["es_dia_atencion"] = ((f.dia_semana_num <= 6) & (f.es_festivo == 0)).astype(int)
    f["tipo_dia"] = "Día hábil"
    f.loc[f.dia_semana_num == 6, "tipo_dia"] = "Sábado (jornada parcial)"
    f.loc[f.dia_semana_num == 7, "tipo_dia"] = "Domingo"
    f.loc[f.es_festivo == 1, "tipo_dia"] = "Festivo"
    f["fecha"] = clave
    guardar(f, "dim_fecha")

    h = pd.DataFrame({"hora": range(24)})
    h["etiqueta"] = h.hora.map(lambda x: f"{x:02d}:00-{x:02d}:59")
    h["franja"] = h.hora.map(franja)
    h["en_horario_atencion"] = h.hora.between(7, 19).astype(int)
    guardar(h, "dim_hora")
    print(len(f), "fechas,", len(h), "horas")
