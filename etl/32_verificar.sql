-- Verificacion de integridad del schema qflow. Todas las columnas "huerfanos" deben dar 0.
USE qflow;

SELECT 'fact_proceso.service_id' AS relacion, COUNT(*) AS huerfanos FROM fact_proceso f LEFT JOIN dim_service d ON f.service_id = d.service_id WHERE d.service_id IS NULL
UNION ALL SELECT 'fact_proceso.last_service_id', COUNT(*) FROM fact_proceso f LEFT JOIN dim_service d ON f.last_service_id = d.service_id WHERE d.service_id IS NULL
UNION ALL SELECT 'fact_proceso.qf_branch_id', COUNT(*) FROM fact_proceso f LEFT JOIN dim_branch d ON f.qf_branch_id = d.qf_branch_id WHERE d.qf_branch_id IS NULL
UNION ALL SELECT 'fact_proceso.customer_id', COUNT(*) FROM fact_proceso f LEFT JOIN dim_customer d ON f.customer_id = d.customer_id WHERE f.customer_id IS NOT NULL AND d.customer_id IS NULL
UNION ALL SELECT 'fact_proceso.officer_id', COUNT(*) FROM fact_proceso f LEFT JOIN dim_officer d ON f.officer_id = d.officer_id WHERE f.officer_id IS NOT NULL AND d.officer_id IS NULL
UNION ALL SELECT 'fact_proceso.fecha_llegada', COUNT(*) FROM fact_proceso f LEFT JOIN dim_date d ON f.arrival_date = d.date WHERE d.date IS NULL
UNION ALL SELECT 'fact_proceso.hora_llegada', COUNT(*) FROM fact_proceso f LEFT JOIN dim_hour d ON f.arrival_hour = d.hour WHERE d.hour IS NULL
UNION ALL SELECT 'fact_proceso.resolution', COUNT(*) FROM fact_proceso f LEFT JOIN dic_resolution d ON f.resolution = d.resolution WHERE d.resolution IS NULL
UNION ALL SELECT 'fact_proceso.last_proc_status_id', COUNT(*) FROM fact_proceso f LEFT JOIN dic_proc_status d ON f.last_proc_status_id = d.proc_status_id WHERE d.proc_status_id IS NULL
UNION ALL SELECT 'puente.process_id', COUNT(*) FROM bridge_process_classification p LEFT JOIN fact_proceso f ON p.process_id = f.process_id WHERE f.process_id IS NULL
UNION ALL SELECT 'puente.classification_id', COUNT(*) FROM bridge_process_classification p LEFT JOIN dim_classification d ON p.classification_id = d.classification_id WHERE d.classification_id IS NULL
UNION ALL SELECT 'fact_oficial_hora.qf_branch_id', COUNT(*) FROM fact_oficial_hora f LEFT JOIN dim_branch d ON f.qf_branch_id = d.qf_branch_id WHERE d.qf_branch_id IS NULL
UNION ALL SELECT 'fact_oficial_hora.fecha', COUNT(*) FROM fact_oficial_hora f LEFT JOIN dim_date d ON f.date = d.date WHERE d.date IS NULL
UNION ALL SELECT 'fact_oficial_hora.officer_status_id', COUNT(*) FROM fact_oficial_hora f LEFT JOIN dic_officer_status d ON f.officer_status_id = d.officer_status_id WHERE d.officer_status_id IS NULL
UNION ALL SELECT 'dim_service.qf_branch_id', COUNT(*) FROM dim_service s LEFT JOIN dim_branch d ON s.qf_branch_id = d.qf_branch_id WHERE s.qf_branch_id IS NOT NULL AND d.qf_branch_id IS NULL
UNION ALL SELECT 'dim_customer.sublevel_id', COUNT(*) FROM dim_customer c LEFT JOIN dic_sublevel d ON c.sublevel_id = d.sublevel_id WHERE c.sublevel_id IS NOT NULL AND d.sublevel_id IS NULL
UNION ALL SELECT 'dim_function_l.function_id', COUNT(*) FROM dim_function_l l LEFT JOIN dim_function_s s ON l.function_id = s.function_id WHERE s.function_id IS NULL;

-- Relaciones declaradas
SELECT TABLE_NAME AS tabla, COLUMN_NAME AS columna, REFERENCED_TABLE_NAME AS referencia, REFERENCED_COLUMN_NAME AS columna_ref
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'qflow' AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY tabla, columna;

-- Controles de negocio
SELECT COUNT(*) AS procesos, SUM(is_abandoned) AS abandonos, ROUND(100 * AVG(is_abandoned), 2) AS pct_abandono,
       MIN(arrival_dt) AS primera_llegada, MAX(arrival_dt) AS ultima_llegada,
       SUM(customer_id IS NULL) AS sin_cliente, SUM(officer_id = -1) AS oficial_desconocido
FROM fact_proceso;
