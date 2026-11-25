-- Schema qflow: modelo en estrella con los datos limpios (CSV en la carpeta Limpio)
-- Hechos: fact_proceso, fact_oficial_hora. Puente: puente_proceso_clasificacion.
-- Dimensiones: dim_branch, dim_service, dim_customer, dim_officer, dim_classification,
-- dim_fecha, dim_hora, dim_function_s, dim_function_l. Diccionarios: dic_*.

DROP SCHEMA IF EXISTS qflow;
CREATE SCHEMA qflow DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE qflow;

-- ---------------------------------------------------------------- diccionarios
CREATE TABLE dic_action (
  action INT PRIMARY KEY,
  description VARCHAR(60), description_en VARCHAR(60), mnemonic VARCHAR(10),
  category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
) COMMENT='Acciones de un paso del proceso';

CREATE TABLE dic_backofficetask (
  backofficetask_id INT PRIMARY KEY,
  description VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
) COMMENT='Tareas de trastienda';

CREATE TABLE dic_customer_level (
  customer_level_id INT PRIMARY KEY,
  description VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
) COMMENT='Segmento del cliente';

CREATE TABLE dic_sublevel (
  sublevel_id INT PRIMARY KEY,
  description VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
) COMMENT='Subsegmento del cliente. 24 a 33 sin descripcion en el origen';

CREATE TABLE dic_occupation (
  occupation_cod VARCHAR(2) COLLATE utf8mb4_bin PRIMARY KEY,
  description VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
);

CREATE TABLE dic_marital_status (
  marital_state VARCHAR(2) COLLATE utf8mb4_bin PRIMARY KEY,
  description VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
);

CREATE TABLE dic_housing_type (
  housing_type VARCHAR(2) COLLATE utf8mb4_bin PRIMARY KEY,
  description VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
);

CREATE TABLE dic_education_level (
  education_level VARCHAR(2) COLLATE utf8mb4_bin PRIMARY KEY,
  description VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
);

CREATE TABLE dic_officer_status (
  officer_status_id INT PRIMARY KEY,
  description VARCHAR(60), description_en VARCHAR(60),
  category VARCHAR(60) COMMENT 'Agrupacion para capacidad', in_original_dictionary TINYINT NOT NULL
);

CREATE TABLE dic_proc_status (
  proc_status_id INT PRIMARY KEY,
  description VARCHAR(60), description_en VARCHAR(60), mnemonic VARCHAR(10), is_waiting TINYINT,
  category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
);

CREATE TABLE dic_resolution (
  resolution INT PRIMARY KEY,
  description VARCHAR(60), description_en VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
);

CREATE TABLE dic_signoutreason (
  signoutreason_id INT PRIMARY KEY,
  description VARCHAR(60), category VARCHAR(60), in_original_dictionary TINYINT NOT NULL
) COMMENT='Motivos de cierre de sesion (reconstruido)';

-- ---------------------------------------------------------------- dimensiones
CREATE TABLE dim_branch (
  qf_branch_id INT PRIMARY KEY,
  qf_branch_type VARCHAR(30),
  zone_name VARCHAR(60),
  zone_name_original VARCHAR(60),
  region VARCHAR(40) COMMENT 'Agrupacion geografica de las zonas (propia del analisis)',
  opens_saturday TINYINT NOT NULL COMMENT '1 si atiende sabados (33 sucursales)'
);

CREATE TABLE dim_service (
  service_id INT PRIMARY KEY,
  service_name VARCHAR(40),
  qf_branch_id INT NULL COMMENT 'Nulo en los 6 servicios no catalogados',
  service_profile_id INT, service_type_id INT, profile_name VARCHAR(40),
  busy_queue_threshold INT, waiting_time_warning INT, waiting_time_critical INT,
  service_time_warning INT, service_time_critical INT,
  waiting_time_standard INT COMMENT 'Estandar de espera en segundos',
  check_short_service_time TINYINT, sst_threshold INT, sst_method TINYINT, sst_no_service_action TINYINT,
  sst_requeue_position INT, sst_requeue_reps INT, manual_requeue_position_in_service INT,
  manual_requeue_position_abandoned INT, on_call_send_audio_message TINYINT, on_call_send_pc_message TINYINT,
  on_call_again_send_audio_message TINYINT, on_call_again_send_pc_message TINYINT, enable_direct_admit TINYINT,
  max_absent_time INT, max_waiting_time INT, max_in_service_time INT, max_on_hold_time INT,
  agent_assignment_type INT, max_waiting_time_target_status INT, max_in_service_time_target_status INT,
  max_on_hold_time_target_status INT, max_waiting_with_rules_time INT,
  service_type_name VARCHAR(30), classification_group_id INT, service_attribute_id INT, attribute_name VARCHAR(40),
  service_name_original VARCHAR(40),
  is_alternative_channel TINYINT NOT NULL,
  is_placeholder TINYINT NOT NULL,
  qf_branch_id_inferred INT COMMENT 'Sucursal inferida por dt_function_s para los no catalogados',
  CONSTRAINT fk_service_branch FOREIGN KEY (qf_branch_id) REFERENCES dim_branch (qf_branch_id)
);

CREATE TABLE dim_customer (
  customer_id INT PRIMARY KEY,
  customer_level_id INT, sublevel_id INT,
  sex CHAR(1),
  birth_year SMALLINT COMMENT 'Perturbado +-2 por anonimato. Nulo si fuera de 1903-2019',
  occupation_cod VARCHAR(2) COLLATE utf8mb4_bin,
  marital_state VARCHAR(2) COLLATE utf8mb4_bin,
  housing_type VARCHAR(2) COLLATE utf8mb4_bin,
  education_level VARCHAR(2) COLLATE utf8mb4_bin,
  registered_svp TINYINT, registered_app TINYINT,
  birth_year_original INT,
  flag_invalid_birth_year TINYINT NOT NULL,
  age_range VARCHAR(20),
  segment_name VARCHAR(60), segment_category VARCHAR(60),
  sublevel_name VARCHAR(60), sublevel_category VARCHAR(60),
  occupation_name VARCHAR(60), occupation_category VARCHAR(60), marital_status_name VARCHAR(60),
  housing_type_name VARCHAR(60), education_level_name VARCHAR(60),
  CONSTRAINT fk_customer_level FOREIGN KEY (customer_level_id) REFERENCES dic_customer_level (customer_level_id),
  CONSTRAINT fk_customer_sublevel FOREIGN KEY (sublevel_id) REFERENCES dic_sublevel (sublevel_id),
  CONSTRAINT fk_customer_occupation FOREIGN KEY (occupation_cod) REFERENCES dic_occupation (occupation_cod),
  CONSTRAINT fk_customer_marital FOREIGN KEY (marital_state) REFERENCES dic_marital_status (marital_state),
  CONSTRAINT fk_customer_housing FOREIGN KEY (housing_type) REFERENCES dic_housing_type (housing_type),
  CONSTRAINT fk_customer_education FOREIGN KEY (education_level) REFERENCES dic_education_level (education_level)
);

CREATE TABLE dim_officer (
  officer_id INT PRIMARY KEY COMMENT '-1 = Desconocido',
  location_name VARCHAR(30), group_name VARCHAR(60),
  group_name_original VARCHAR(60) COMMENT 'Grupo tal como venia en la fuente',
  group_category VARCHAR(40) COMMENT 'Familia funcional: Caja, Asesoria, Direccion, ...',
  hire_date DATE, flag_invalid_hire_date TINYINT NOT NULL,
  hire_date_alternate DATE COMMENT 'Segunda fecha de los ids que venian duplicados',
  is_placeholder TINYINT NOT NULL
);

CREATE TABLE dim_classification (
  classification_id INT PRIMARY KEY,
  classification_name VARCHAR(60),
  classification_group_ids VARCHAR(10) COMMENT 'Lista de grupos: 5/16 en los ids multigrupo',
  group_name VARCHAR(80), parent_group_id INT,
  is_multigroup TINYINT NOT NULL
);

CREATE TABLE dim_date (
  date DATE PRIMARY KEY,
  year SMALLINT, month TINYINT, month_name VARCHAR(12), year_month_key CHAR(7), iso_week TINYINT,
  day TINYINT, weekday_num TINYINT COMMENT '1 = lunes', weekday_name VARCHAR(10),
  fortnight TINYINT, is_weekend TINYINT, is_payday TINYINT,
  is_holiday TINYINT, holiday_name VARCHAR(40),
  is_business_day TINYINT COMMENT 'Dia habil bancario: lunes a viernes sin festivos',
  is_operating_day TINYINT COMMENT 'Dia de atencion en sucursal: lunes a sabado sin festivos',
  day_type VARCHAR(30) COMMENT 'Dia habil, Sabado (jornada parcial), Domingo o Festivo'
);

CREATE TABLE dim_hour (
  hour TINYINT PRIMARY KEY,
  label CHAR(11), time_band VARCHAR(20), is_business_hours TINYINT
);

CREATE TABLE dim_function_s (
  function_id INT PRIMARY KEY,
  qf_branch_id INT COMMENT 'Toda la red: sin FK a dim_branch',
  prio_services VARCHAR(80),
  in_study TINYINT NOT NULL
);

CREATE TABLE dim_function_l (
  function_id INT NOT NULL,
  service_id INT NOT NULL COMMENT 'Toda la red: sin FK a dim_service',
  priority TINYINT,
  in_study TINYINT NOT NULL,
  service_in_dim_service TINYINT NOT NULL,
  PRIMARY KEY (function_id, service_id),
  CONSTRAINT fk_function_l_s FOREIGN KEY (function_id) REFERENCES dim_function_s (function_id)
);

-- ---------------------------------------------------------------- hechos
CREATE TABLE fact_proceso (
  process_id INT PRIMARY KEY,
  arrival_dt DATETIME(3) NOT NULL,
  service_id INT NOT NULL,
  qf_branch_id INT NOT NULL,
  customer_id INT NULL,
  q_code CHAR(1), q_number SMALLINT,
  last_proc_status_id INT NOT NULL,
  last_update_dt DATETIME(3) NOT NULL,
  last_service_id INT NOT NULL,
  resolution INT NOT NULL,
  total_time_sec DECIMAL(12,3),
  n_steps SMALLINT,
  wait_sec INT, service_sec INT, hold_sec INT,
  n_calls SMALLINT, n_transfers SMALLINT,
  officer_id INT NULL COMMENT '-1 = oficial sin registro',
  classifications VARCHAR(80),
  is_abandoned TINYINT NOT NULL,
  arrival_date DATE NOT NULL,
  arrival_hour TINYINT NOT NULL,
  officer_id_original INT,
  unexplained_time_sec DECIMAL(12,3),
  flag_wait_over_standard TINYINT NULL,
  flag_alternative_channel TINYINT NOT NULL,
  flag_holiday TINYINT NOT NULL,
  flag_no_service TINYINT NOT NULL,
  flag_batch_close TINYINT NOT NULL,
  flag_closed_other_day TINYINT NOT NULL,
  flag_off_hours TINYINT NOT NULL,
  flag_low_volume_day TINYINT NOT NULL,
  flag_high_volume_day TINYINT NOT NULL,
  flag_wait_outlier TINYINT NOT NULL,
  flag_short_service TINYINT NOT NULL,
  flag_long_service TINYINT NOT NULL,
  flag_has_transfer TINYINT NOT NULL,
  CONSTRAINT fk_proceso_service FOREIGN KEY (service_id) REFERENCES dim_service (service_id),
  CONSTRAINT fk_proceso_last_service FOREIGN KEY (last_service_id) REFERENCES dim_service (service_id),
  CONSTRAINT fk_proceso_branch FOREIGN KEY (qf_branch_id) REFERENCES dim_branch (qf_branch_id),
  CONSTRAINT fk_proceso_customer FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id),
  CONSTRAINT fk_proceso_officer FOREIGN KEY (officer_id) REFERENCES dim_officer (officer_id),
  CONSTRAINT fk_proceso_status FOREIGN KEY (last_proc_status_id) REFERENCES dic_proc_status (proc_status_id),
  CONSTRAINT fk_proceso_resolution FOREIGN KEY (resolution) REFERENCES dic_resolution (resolution),
  CONSTRAINT fk_proceso_fecha FOREIGN KEY (arrival_date) REFERENCES dim_date (date),
  CONSTRAINT fk_proceso_hora FOREIGN KEY (arrival_hour) REFERENCES dim_hour (hour)
);

CREATE TABLE bridge_process_classification (
  process_id INT NOT NULL,
  classification_id INT NOT NULL,
  PRIMARY KEY (process_id, classification_id),
  CONSTRAINT fk_puente_proceso FOREIGN KEY (process_id) REFERENCES fact_proceso (process_id),
  CONSTRAINT fk_puente_clasificacion FOREIGN KEY (classification_id) REFERENCES dim_classification (classification_id)
);

CREATE TABLE fact_oficial_hora (
  id INT AUTO_INCREMENT PRIMARY KEY,
  date DATE NOT NULL,
  hour TINYINT NOT NULL,
  qf_branch_id INT NOT NULL,
  officer_status_id INT NOT NULL,
  n_events INT, n_officers INT,
  duration_sec BIGINT COMMENT 'Suma de duracion de eventos iniciados en la hora, en segundos',
  flag_exceeds_hour TINYINT NOT NULL,
  duration_sec_capped BIGINT COMMENT 'min(duration_sec, n_officers x 3600)',
  flag_off_hours TINYINT NOT NULL,
  UNIQUE KEY uq_grano (date, hour, qf_branch_id, officer_status_id),
  CONSTRAINT fk_ofh_fecha FOREIGN KEY (date) REFERENCES dim_date (date),
  CONSTRAINT fk_ofh_hora FOREIGN KEY (hour) REFERENCES dim_hour (hour),
  CONSTRAINT fk_ofh_branch FOREIGN KEY (qf_branch_id) REFERENCES dim_branch (qf_branch_id),
  CONSTRAINT fk_ofh_status FOREIGN KEY (officer_status_id) REFERENCES dic_officer_status (officer_status_id)
);
