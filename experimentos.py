import pandas as pd

from entorno import generar_entorno
from social import decidir_llegadas
from hospital import simular_hospital
from metricas import calcular_metricas


def ejecutar_experimentos(replicas=10):
    resultados = []

    escenarios = [
        ("S1 - Sin influencia", 0, False, False),
        ("S2 - Con influencia", 3, False, False),
        ("S3 - Con medidas", 3, True, True)
    ]

    for nombre, beta, orientacion, refuerzo in escenarios:
        for semilla in range(replicas):
            entorno = generar_entorno(semilla)

            llegadas = decidir_llegadas(
                entorno,
                beta=beta,
                orientacion=orientacion
            )

            resultado = simular_hospital(
                llegadas,
                refuerzo=refuerzo
            )

            fila = calcular_metricas(resultado)
            fila["escenario"] = nombre
            fila["replica"] = semilla
            resultados.append(fila)

    return pd.DataFrame(resultados)


def resumir_resultados(datos):
    columnas = [
        "llegadas",
        "atendidos",
        "pendientes",
        "espera_media",
        "cola_maxima"
    ]

    return datos.groupby("escenario")[columnas].mean().round(2)