import numpy as np
from params import DURACION, PASO, BETA, TIEMPO_ORIENTACION


def decidir_llegadas(entorno, beta=BETA, orientacion=False):
    rng = np.random.default_rng(entorno["semilla"])

    gravedad = entorno["gravedad"]
    contactos = entorno["contactos"]
    n = len(gravedad)

    decidio = np.zeros(n, dtype=bool)
    llegadas = []

    # Probabilidad base de llegada por minuto
    tasas = [0.025, 0.016, 0.0125]
    influencia = [0.15, 0.60, 1.0]

    for tiempo in range(0, DURACION, PASO):
        for i in range(n):
            if decidio[i]:
                continue

            vecinos = contactos[i]
            fraccion = np.mean(decidio[vecinos])

            tasa = tasas[gravedad[i]]
            tasa *= 1 + beta * influencia[gravedad[i]] * fraccion

            # Después de la orientación, algunas llegadas se evitan
            if orientacion and tiempo >= TIEMPO_ORIENTACION:
                tasa *= 0.60

            probabilidad = 1 - np.exp(-tasa * PASO)

            if rng.random() < probabilidad:
                decidio[i] = True
                llegadas.append({
                    "id": i,
                    "llegada": tiempo,
                    "gravedad": int(gravedad[i]),
                    "tipo": "sismo"
                })

    return llegadas