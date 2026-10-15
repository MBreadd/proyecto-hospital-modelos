import numpy as np
from params import NUM_PERSONAS


def generar_entorno(semilla=1):
    rng = np.random.default_rng(semilla)

    # Gravedad de cada persona: 0 grave, 1 moderado, 2 leve
    gravedad = rng.choice(
        [0, 1, 2],
        size=NUM_PERSONAS,
        p=[0.10, 0.30, 0.60]
    )

    # Cada persona tiene seis contactos distintos
    contactos = []
    for i in range(NUM_PERSONAS):
        posibles = [j for j in range(NUM_PERSONAS) if j != i]
        vecinos = rng.choice(posibles, size=6, replace=False)
        contactos.append(vecinos)

    return {
        "semilla": semilla,
        "gravedad": gravedad,
        "contactos": contactos
    }