import numpy as np
from params import (
    DURACION, PASO, TRIAJES, EQUIPOS, CAMAS,
    TIEMPO_REFUERZO, TIEMPO_ATENCION, TIEMPO_ESTANCIA
)


def simular_hospital(llegadas, refuerzo=False):
    cola_triaje = []
    cola_atencion = []

    triajes_activos = []
    atenciones_activas = []
    camas_activas = []

    tiempos_espera = []
    atendidos = 0
    max_cola = 0

    equipos = EQUIPOS
    camas = CAMAS

    llegadas = sorted(llegadas, key=lambda p: p["llegada"])
    siguiente = 0

    for tiempo in range(0, DURACION, PASO):

        # Activar recursos adicionales
        if refuerzo and tiempo >= TIEMPO_REFUERZO:
            equipos = EQUIPOS + 4
            camas = CAMAS + 10

        # Liberar recursos que terminaron su trabajo
        triajes_activos = [
            p for p in triajes_activos if p["fin"] > tiempo
        ]

        terminadas = [
            p for p in atenciones_activas if p["fin"] <= tiempo
        ]
        atenciones_act = [
            p for p in atenciones_activas if p["fin"] > tiempo
        ]
        atenciones_activas = atenciones_act

        # Contar pacientes atendidos
        for paciente in terminadas:
            atendidos += 1

        camas_activas = [
            fin for fin in camas_activas if fin > tiempo
        ]

        # Incorporar pacientes que ya llegaron
        while (
            siguiente < len(llegadas)
            and llegadas[siguiente]["llegada"] <= tiempo
        ):
            cola_triaje.append(llegadas[siguiente])
            siguiente += 1

        # Atender el triaje
        while cola_triaje and len(triajes_activos) < TRIAJES:
            paciente = cola_triaje.pop(0)
            paciente["fin_triaje"] = tiempo + PASO
            triajes_activos.append({
                "fin": tiempo + PASO,
                "paciente": paciente
            })

        # Pasar a atención a quienes terminaron el triaje
        terminan_triaje = [
            p for p in triajes_activos if p["fin"] <= tiempo + PASO
        ]
        for trabajo in terminan_triaje:
            paciente = trabajo["paciente"]
            if paciente not in cola_atencion:
                cola_atencion.append(paciente)

        # Evitar volver a incorporar el mismo triaje
        triajes_activos = [
            p for p in triajes_activos if p["fin"] > tiempo + PASO
        ]

        # Priorizar pacientes más graves: gravedad 0 es la más alta
        cola_atencion.sort(key=lambda p: (p["gravedad"], p["llegada"]))

        # Iniciar atención si hay equipos disponibles
        while cola_atencion and len(atenciones_activas) < equipos:
            paciente = cola_atencion[0]
            gravedad = paciente["gravedad"]

            necesita_cama = gravedad < 2
            if necesita_cama and len(camas_activas) >= camas:
                break

            cola_atencion.pop(0)

            espera = tiempo - paciente["llegada"]
            tiempos_espera.append(espera)

            duracion = TIEMPO_ATENCION[gravedad]
            fin = tiempo + max(PASO, round(duracion / PASO) * PASO)

            atenciones_activas.append({
                "fin": fin,
                "gravedad": gravedad
            })

            if necesita_cama:
                estancia = TIEMPO_ESTANCIA[gravedad]
                camas_activas.append(fin + estancia)

        max_cola = max(
            max_cola,
            len(cola_triaje) + len(cola_atencion)
        )

    pendientes = len(llegadas) - atendidos

    return {
        "llegadas": len(llegadas),
        "atendidos": atendidos,
        "pendientes": pendientes,
        "espera_media": (
            float(np.mean(tiempos_espera)) if tiempos_espera else 0
        ),
        "cola_maxima": max_cola
    }