"""Rutas, lectura de CSV originales y credenciales de MySQL para el proyecto Qflow."""
import os
from pathlib import Path

import pandas as pd

# Carpeta raiz con Fuente\, Limpio\ y Limpieza\. Por defecto, la carpeta que contiene a etl\.
BASE = Path(os.getenv("QFLOW_BASE", Path(__file__).resolve().parent.parent))
FUENTE = BASE / "Fuente"
DATOS = FUENTE / "datos"
DICS = FUENTE / "diccionarios"
LIMPIO = BASE / "Limpio"
BITACORA = BASE / "Limpieza" / "bitacora_limpieza.md"

# Credenciales por variables de entorno: no se guardan en el codigo.
MYSQL = dict(host=os.getenv("QFLOW_MYSQL_HOST", "localhost"), port=int(os.getenv("QFLOW_MYSQL_PORT", "3306")),
             user=os.getenv("QFLOW_MYSQL_USER", "root"), password=os.getenv("QFLOW_MYSQL_PASSWORD", ""),
             database="qflow")

NULOS = [r"\N", ""]

# Etiqueta unica para todo valor que no se conoce (nulos, grupos vacios, placeholders) en todas las dimensiones.
# No se usa para "No aplica" (el atributo no corresponde) ni para "Codigo X (sin descripcion)" (el codigo existe).
SIN_IDENTIFICAR = "Sin identificar"

# Nombres de columna en snake_case para todo el modelo. Los originales de Qflow venian pegados
# (profilename, waitingtimestandard). Tambien se unifican las claves que nombraban lo mismo de dos
# formas (oficial_id en fact_proceso y officer_id en dim_officer). Se aplica al guardar cada CSV limpio.
RENOMBRAR = {
    # dim_service
    "servicename": "service_name", "servicename_original": "service_name_original",
    "serviceprofile_id": "service_profile_id", "servicetype_id": "service_type_id",
    "servicetypename": "service_type_name", "profilename": "profile_name",
    "serviceattribute_id": "service_attribute_id", "attributename": "attribute_name",
    "busyqueuethreshold": "busy_queue_threshold", "waitingtimewarning": "waiting_time_warning",
    "waitingtimecritical": "waiting_time_critical", "servicetimewarning": "service_time_warning",
    "servicetimecritical": "service_time_critical", "waitingtimestandard": "waiting_time_standard",
    "checkshortservicetime": "check_short_service_time", "sstthreshold": "sst_threshold",
    "sstmethod": "sst_method", "sstnoserviceaction": "sst_no_service_action",
    "sstrequeueposition": "sst_requeue_position", "sstrequeuereps": "sst_requeue_reps",
    "manualrequeuepositioninservice": "manual_requeue_position_in_service",
    "manualrequeuepositionabandoned": "manual_requeue_position_abandoned",
    "oncallsendaudiomessage": "on_call_send_audio_message", "oncallsendpcmessage": "on_call_send_pc_message",
    "oncallagainsendaudiomessage": "on_call_again_send_audio_message",
    "oncallagainsendpcmessage": "on_call_again_send_pc_message", "enabledirectadmit": "enable_direct_admit",
    "maxabsenttime": "max_absent_time", "maxwaitingtime": "max_waiting_time",
    "maxinservicetime": "max_in_service_time", "maxonholdtime": "max_on_hold_time",
    "agentassignmenttype": "agent_assignment_type",
    "maxwaitingtimetargetstatus": "max_waiting_time_target_status",
    "maxinservicetimetargetstatus": "max_in_service_time_target_status",
    "maxonholdtimetargetstatus": "max_on_hold_time_target_status",
    "maxwaitingwithrulestime": "max_waiting_with_rules_time",
    # dim_service y dim_classification
    "classificationgroup_id": "classification_group_id",
    # dim_classification y dim_officer
    "groupname": "group_name", "parentgroup_id": "parent_group_id",
    # fact_proceso
    "qcode": "q_code", "qnumber": "q_number", "last_proc_status": "last_proc_status_id",
    "oficial_id": "officer_id", "oficial_id_origen": "officer_id_original",
    # Columnas en espanol (metricas de la fuente y columnas agregadas en la limpieza) pasan a ingles,
    # el idioma mayoritario de la fuente. Las equivalencias con los nombres del PDF estan en la bitacora.
    "tiempo_total_seg": "total_time_sec", "n_pasos": "n_steps", "espera_seg": "wait_sec",
    "atencion_seg": "service_sec", "retenido_seg": "hold_sec", "n_llamados": "n_calls",
    "n_transferencias": "n_transfers", "clasificaciones": "classifications", "abandono": "is_abandoned",
    "fecha_llegada": "arrival_date", "hora_llegada": "arrival_hour",
    "tiempo_no_explicado_seg": "unexplained_time_sec",
    "flag_espera_sobre_estandar": "flag_wait_over_standard", "flag_canal_alternativo": "flag_alternative_channel",
    "flag_festivo": "flag_holiday", "flag_sin_atencion": "flag_no_service", "flag_cierre_lote": "flag_batch_close",
    "flag_cierre_otro_dia": "flag_closed_other_day", "flag_fuera_horario": "flag_off_hours",
    "flag_dia_volumen_bajo": "flag_low_volume_day", "flag_dia_volumen_alto": "flag_high_volume_day",
    "flag_espera_atipica": "flag_wait_outlier", "flag_atencion_corta": "flag_short_service",
    "flag_atencion_larga": "flag_long_service",
    "flag_con_transferencia": "flag_has_transfer",
    # fact_oficial_hora
    "fecha": "date", "hora": "hour", "n_eventos": "n_events", "n_oficiales": "n_officers",
    "seg": "duration_sec", "seg_tope_hora": "duration_sec_capped", "flag_excede_hora": "flag_exceeds_hour",
    # diccionarios
    "descripcion": "description", "desc_ingles": "description_en", "mnemonico": "mnemonic",
    "categoria": "category", "en_diccionario_original": "in_original_dictionary", "esperando": "is_waiting",
    # dimensiones
    "nombre_zona": "zone_name", "nombre_zona_original": "zone_name_original", "multigrupo": "is_multigroup",
    "flag_birth_year_invalido": "flag_invalid_birth_year", "rango_edad": "age_range",
    "flag_hire_date_invalida": "flag_invalid_hire_date", "hire_date_alterna": "hire_date_alternate",
    "es_placeholder": "is_placeholder", "es_canal_alternativo": "is_alternative_channel",
    "qf_branch_id_inferida": "qf_branch_id_inferred", "en_estudio": "in_study",
    "servicio_en_dim_service": "service_in_dim_service",
    # dim_date (year_month es palabra reservada en MySQL, por eso year_month_key)
    "anio": "year", "mes": "month", "nombre_mes": "month_name", "anio_mes": "year_month_key",
    "semana_iso": "iso_week", "dia": "day", "dia_semana_num": "weekday_num", "dia_semana": "weekday_name",
    "quincena": "fortnight", "es_fin_de_semana": "is_weekend", "es_dia_pago": "is_payday",
    "es_festivo": "is_holiday", "nombre_festivo": "holiday_name", "es_dia_habil": "is_business_day",
    "es_dia_atencion": "is_operating_day", "tipo_dia": "day_type", "atiende_sabado": "opens_saturday",
    # dim_hour
    "etiqueta": "label", "franja": "time_band", "en_horario_atencion": "is_business_hours",
}

# Tablas creadas en la limpieza con nombre en espanol. fact_proceso y fact_oficial_hora conservan
# el nombre que fija el PDF del proyecto.
TABLAS = {"dim_fecha": "dim_date", "dim_hora": "dim_hour",
          "puente_proceso_clasificacion": "bridge_process_classification"}


def ruta(nombre):
    """Devuelve la ruta del CSV original, buscando en datos\\ y en diccionarios\\."""
    for carpeta in (DATOS, DICS):
        p = carpeta / f"{nombre}.csv"
        if p.exists():
            return p
    raise FileNotFoundError(nombre)


def codificacion(p):
    """UTF-8 si todo el archivo decodifica como UTF-8, si no latin-1 (problema conocido del PDF)."""
    try:
        p.read_bytes().decode("utf-8")
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "latin-1"


def leer(nombre, como_texto=True, **kw):
    """Lee un CSV original. Por defecto todo como texto, para no perder ceros a la izquierda ni espacios."""
    p = ruta(nombre)
    opciones = dict(na_values=NULOS, keep_default_na=False, low_memory=False)
    if como_texto:
        opciones["dtype"] = str
    opciones.update(kw)
    if p.stat().st_size > 50_000_000:
        # archivos grandes (hechos y clientes) son UTF-8 valido y con fin de linea normal
        return pd.read_csv(p, encoding="utf-8", **opciones)
    texto = p.read_bytes().decode(codificacion(p))
    # dic_signoutreason_id.csv usa solo CR como fin de linea
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    from io import StringIO
    return pd.read_csv(StringIO(texto), **opciones)


def guardar(df, nombre):
    """Guarda el CSV limpio en UTF-8, con nulos como \\N para LOAD DATA de MySQL."""
    LIMPIO.mkdir(exist_ok=True)
    salida = LIMPIO / f"{TABLAS.get(nombre, nombre)}.csv"
    df = df.rename(columns=RENOMBRAR)
    df.to_csv(salida, index=False, encoding="utf-8", na_rep=r"\N", lineterminator="\n")
    return salida
