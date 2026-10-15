# Simulación de Saturación Hospitalaria ante Emergencias Masivas
**Comportamiento colectivo + eventos discretos** · Proyecto final de Modelos y Simulación · *Avance (primera mitad)*

Un hospital ficticio recibe pacientes durante las 6 horas posteriores a un sismo. Cada persona decide **cuándo**
acudir y esa decisión se ve influida por sus contactos cercanos (red social). Las llegadas alimentan una
**simulación de eventos discretos** con triaje, colas por gravedad, camas y equipos de atención limitados.

> Todos los parámetros son **supuestos académicos** (ver `params.py`). No es una predicción de un hospital real.

## Cómo correrlo

```bash
pip install -r requirements.txt
python pruebas.py          # verifica el código (conservación, capacidad, prioridad, reproducibilidad)
python validacion_mmc.py   # valida el motor de eventos contra la teoría (Erlang C)
python main.py             # 200 réplicas x 3 escenarios + barrido de β + ablación + volumen vs concentración (~10 s)
python graficos.py         # genera resultados/figuras/*.png
```

## Escenarios

| | Descripción |
|---|---|
| **S1** | Llegadas **sin** influencia social (β = 0) |
| **S2** | Llegadas **con** influencia social (β = 3) |
| **S3** | S2 + orientación a la población (desde el min 60) + refuerzo temporal de atención (desde el min 90) |

Las tres comparten los mismos números aleatorios en cada réplica (CRN), así que las diferencias se comparan de forma pareada.

## Estructura y responsables sugeridos (3 integrantes)

| Archivo | Qué hace | Responsable |
|---|---|---|
| `params.py` | Todos los parámetros (un solo lugar) | todos |
| `entorno.py`, `social.py` | Red de contactos, regla de influencia social, llegadas | **A · Comportamiento colectivo** |
| `hospital.py`, `pruebas.py`, `validacion_mmc.py` | Motor de eventos discretos, triaje, colas, recursos, verificación y validación | **B · Hospital y eventos discretos** |
| `metricas.py`, `experimentos.py`, `main.py`, `graficos.py` | Indicadores, réplicas, estadística, figuras | **C · Experimentos y resultados** |

## Resultados (carpeta `resultados/`)

`metricas_por_replica.csv` · `resumen.csv` · `diferencias_pareadas.csv` · `barrido_beta.csv` ·
`ablacion_medidas.csv` · `descomposicion_volumen.csv` · `series.pkl` · `figuras/`

## Límites conocidos (para la segunda mitad)

- Parámetros sin calibrar con datos reales; falta justificarlos con literatura y análisis de sensibilidad.
- Un solo hospital: los pacientes derivados por la orientación **desaparecen** del sistema (no se modela dónde terminan).
- No hay abandono de la cola, ni zona separada para leves, ni interrupción de atención por pacientes más graves.
- Con estos parámetros el hospital se congestiona pero **termina** de atender a todos en 6 h (pendientes al cierre ≈ 0): falta una prueba de estrés (más pacientes / menos recursos).
- La influencia social cambia **a la vez** el volumen y la concentración de llegadas; `descomposicion_volumen.csv` separa ambos efectos de forma aproximada.
