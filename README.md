# Eficiencia del servicio en sucursales bancarias con Power BI (Qflow)

Proyecto aplicado de la Especialización en Machine Learning de la Universidad del Magdalena. Analiza 2.394.459 visitas a 56 sucursales de un banco colombiano, registradas entre el 1 de agosto y el 31 de octubre de 2017 en Qflow, el sistema de gestión de filas del banco. Busca dónde y por qué las visitas esperan más que el estándar de su servicio, y qué acciones reducirían la espera y el abandono.

Autoras: Yirleidis Andrea Marquez Cortes y Melani Juliana Tirado Salas.

## Archivos principales

| Archivo | Contenido |
|---|---|
| [Informe_gerencial_Qflow.pdf](Informe_gerencial_Qflow.pdf) | Informe para la gerencia (7 páginas): resumen ejecutivo, metodología, hallazgos, propuestas con línea base y meta, y limitaciones. |
| [Reporte_Qflow.pbix](Reporte_Qflow.pbix) | Dashboard de Power BI con 9 páginas, una página de detalle por sucursal y fichas emergentes. Pesa unos 86 MB: GitHub no lo muestra en el navegador, así que se descarga con el botón "Download raw file" y se abre en Power BI Desktop. |
| [plan_analitico/](plan_analitico/) | Plan analítico: problema, decisiones del modelo de datos, verificaciones, las 12 preguntas con su hipótesis y el diseño de las páginas. |
| [etl/](etl/) | Scripts de Python y SQL que limpian las tablas originales, crean el modelo en MySQL, lo cargan y auditan el resultado. |

## El problema

En el trimestre, el 37,7 % de las visitas esperó más que el estándar de su servicio (901.808 visitas) y el 13,3 % terminó abandonada (317.559 visitas). La espera mediana fue de 17,6 minutos, y 1 de cada 10 visitas esperó más de 57 minutos.

## Cómo se trabajó

El problema se dividió en cinco posibles causas sin solapamiento: capacidad, asignación de oficiales, proceso de atención, diseño del estándar y formato de sucursal. Cada causa se convirtió en preguntas con una hipótesis que los datos podían confirmar o refutar (12 preguntas en cinco ejes: espera, abandono, clientes, capacidad y proceso).

Para que las hipótesis no se ajustaran a los mismos datos que las prueban, el período se dividió en dos. Cada hipótesis y cada corte se fijaron con agosto y septiembre (1.613.307 procesos) y se comprobaron con octubre (781.152 procesos). El informe distingue lo que se repitió en octubre de lo que no, y lo observado de lo inferido.

Antes de analizar se hicieron cuatro verificaciones de calidad:

1. La espera, la atención y la retención explican el 96,6 % del tiempo total en las visitas completadas y el 70,6 % en las abandonadas.
2. El volumen diario se mueve entre 30.183 y 37.455 visitas, con tres festivos atípicos y sin domingos.
3. Solo se excluyeron los canales alternativos (170 procesos, 0,01 %). No se recortaron esperas atípicas, cierres por lote ni días de bajo volumen, para no ocultar los casos que más afectan al cliente.
4. Cada cifra del dashboard se validó contra el análisis.

## Datos y modelo

Las tablas originales de Qflow (procesos, eventos de oficiales por hora, sucursales, servicios, oficiales, clientes y 12 diccionarios) se limpiaron en Python y se cargaron a MySQL en un modelo en estrella:

- **Hechos:** `fact_proceso` (2.394.629 procesos) y `fact_oficial_hora` (176.764 filas de estado de los oficiales por hora), con una tabla puente entre procesos y clasificaciones.
- **Dimensiones:** sucursal, servicio, cliente (776.980), oficial, clasificación, función, y calendarios propios de fecha (con quincena, día de pago y festivos de Colombia) y de hora.
- **Limpieza:** ninguna regla borra filas, todas marcan. Se repararon textos con codificación dañada ("NARI#O" a "Nariño"), se unificaron códigos duplicados de los diccionarios, el año de nacimiento con ruido de anonimización pasó a rangos de edad, y los registros sin correspondencia quedaron como "Sin identificar". Se agregaron marcas de espera atípica (más de Q3 + 3 IQR por tipo de servicio), días de volumen anormal (z robusto mayor que 3,5) y cierres por lote, entre otras.
- **Auditoría:** después de la carga, scripts que revisan cada columna, el tipo de dato frente a su contenido, valores parecidos que podrían significar lo mismo y el linaje de cada columna desde la fuente.

En Power BI, las 184 medidas DAX están agrupadas por carpetas en una tabla de medidas, las claves están ocultas y las medianas más pesadas se precalculan en Power Query.

## Páginas del dashboard

| Página | Pregunta que responde |
|---|---|
| 1. Resumen | Cómo está el servicio: cuatro indicadores con semáforo y variación mensual, tendencia diaria y hallazgos principales. |
| 2. Espera | Dónde y cuándo se incumple el estándar (mapa de calor de día por hora, servicios y zonas). |
| 3. Abandono | Qué explica el abandono: curva por tramo de espera y sucursales que abandonan más de lo esperado. |
| 4. Clientes | Si los segmentos esperan y abandonan igual, y el efecto del canal digital. |
| 5. Capacidad | Cómo se comparan las llegadas con los oficiales disponibles y sus estados por hora. |
| 6. Ocupación | Por qué sucursales parecidas incumplen distinto. |
| 7. Proceso | Si la demora viene del servicio, de los oficiales o del estándar. |
| 8. Qué hacer | Simuladores de reducción de espera y de ajuste del estándar, acciones y sucursales para empezar. |
| 9. Metodología | Definiciones, filtros, verificaciones y limitaciones. |

## Hallazgos principales

1. **El incumplimiento se concentra en cinco horas y en la asesoría.** De 10 a 12 h y de 15 a 16 h ocurre el 57,7 % de los incumplimientos. Asesoría Básica incumple en el 63,9 % de sus visitas y Asesoría Prioritaria en el 58,5 %, mientras que Caja General aporta el mayor volumen (52,8 % de los incumplimientos).
2. **El abandono crece con la espera, de 5 % a 44 %.** Con menos de 5 minutos de espera abandona el 5,3 % de las visitas, y con más de 2 horas, el 43,6 %. La curva de agosto y septiembre predijo la de octubre con un error medio de 0,25 puntos por tramo. El 62,1 % de los abandonos ocurrió cuando la cola ya superaba el estándar, así que el abandono no se explica solo por clientes que no se presentan al llamado.
3. **Las sucursales con oficiales más ocupados incumplen más.** El cuarto de sucursales más ocupadas (14 sucursales, con más del 76,8 % del tiempo disponible atendiendo) incumple en el 48,0 % de sus visitas, frente al 27,9 % del cuarto menos ocupado.
4. **Los días críticos se pueden anticipar.** Son los primeros días de operación del mes y el día siguiente a un festivo: 8 días que reúnen el 22,1 % de los incumplimientos.

## Recomendación

Reforzar la atención de 10 a 12 h y de 15 a 16 h en las 14 sucursales más ocupadas, empezando por un piloto en la sucursal 158 (Cartagena). Esa sucursal incumple en el 67,3 % de las visitas y, a la vez, sus oficiales están libres el 29,3 % del tiempo a las 16 h, por eso el piloto verifica primero si los oficiales que quedan libres en las horas de mayor espera pueden atender las colas que esperan.

Si la espera bajara un 20 % en esas horas y sucursales, y la relación entre espera y abandono del trimestre se mantuviera, el abandono de esas visitas pasaría del 16,7 % al 14,5 %: unos 8.400 abandonos menos por trimestre. Es una estimación para dimensionar la acción, no una promesa. Solo un piloto con sucursales de comparación puede confirmar el efecto.

## Limitaciones

Todas las relaciones del análisis son asociaciones, no efectos causales. La hora de cierre de los abandonos no es la hora real de salida del cliente (el 71,8 % se cierra por lote), y los datos por hora no identifican a cada oficial, así que no muestran qué colas atendía un oficial libre. Las cifras son de 2017: describen un caso de estudio, no el estado actual de la red.

## Cómo ejecutar el ETL

Los datos originales de Qflow no se incluyen en el repositorio. Para reproducir la limpieza y la carga se necesitan Python 3, pandas, NumPy, PyMySQL y MySQL 8.

1. Poner las tablas originales en `Fuente/datos/` y los diccionarios en `Fuente/diccionarios/`, en la carpeta que contiene a `etl/`. Otra ubicación se indica con la variable de entorno `QFLOW_BASE`.
2. Definir las credenciales de MySQL con variables de entorno: `QFLOW_MYSQL_USER`, `QFLOW_MYSQL_PASSWORD` y, si hace falta, `QFLOW_MYSQL_HOST`, `QFLOW_MYSQL_PORT` y `QFLOW_MYSQL_EXE` (ruta de `mysql.exe`).
3. Ejecutar `python etl/50_ejecutar_todo.py`. El proceso limpia cada tabla, crea el schema, carga los datos con verificación de conteos y sumas de control, y corre las auditorías. Cada paso se detiene si falla.

## Herramientas

Power BI Desktop (DAX, Power Query y modelado en estrella), Python (pandas y NumPy), MySQL y SQL.
