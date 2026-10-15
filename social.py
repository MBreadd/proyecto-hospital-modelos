"""
social.py  -  Comportamiento colectivo: ¿cuándo decide cada persona acudir al hospital?

Cada persona vive en una red de contactos cercanos. En cada paso de tiempo (dt min),
una persona que aún no decidió acude con probabilidad

    p_i = 1 - exp(-h_i * dt),    h_i = h_base[grav] * g(t) * (1 + beta * suscept[grav] * f_i)

donde g(t) es la forma "natural" de la respuesta tras el sismo (pico en t0) y
f_i es la fracción de contactos de i que YA decidieron ir a este hospital.
Con beta = 0 no hay influencia social (Escenario 1).

Esta regla es una HIPÓTESIS DEL MODELO, no una afirmación sobre un hospital real.
Salida: instante de llegada de cada persona (NaN si no llega) -> alimenta hospital.py
"""
import numpy as np

from entorno import Entorno
from params import Params


def decidir_llegadas(env: Entorno, prm: Params) -> dict:
    N = prm.N
    pasos = env.U.shape[1]
    idx = env.sev - 1
    h_base = np.array(prm.h_base)[idx]
    suscept = np.array(prm.suscept)[idx]
    p_der = np.array(prm.p_derivar)[idx]

    decidio = np.zeros(N, dtype=bool)     # ya decidió (venir aquí o ir a otro lugar)
    va_aqui = np.zeros(N, dtype=bool)     # decidió venir a ESTE hospital
    derivado = np.zeros(N, dtype=bool)    # fue orientado a otro establecimiento
    t_arr = np.full(N, np.nan)
    frac_aqui = np.zeros(pasos)

    for k in range(pasos):
        t = k * prm.dt
        tm = t + prm.dt / 2.0
        g = (tm / prm.t0_pico) * np.exp(1.0 - tm / prm.t0_pico)

        f = env.adj @ va_aqui.astype(float) / env.deg       # presión social de los contactos
        orientando = prm.t_orient is not None and tm >= prm.t_orient
        w = (1.0 - prm.efecto_orient) if orientando else 1.0  # la orientación amortigua la influencia

        h = h_base * g * (1.0 + prm.beta * suscept * f * w)
        p = 1.0 - np.exp(-h * prm.dt)

        nuevo = (~decidio) & (env.U[:, k] < p)

        if orientando:                                       # parte de los que decidían se deriva
            der = nuevo & (env.V[:, k] < p_der)
            derivado |= der
            decidio |= der
            nuevo &= ~der

        # Dado que U < p, U/p es uniforme(0,1): sirve para ubicar la llegada dentro del intervalo
        t_arr[nuevo] = t + prm.dt * (env.U[nuevo, k] / p[nuevo])
        va_aqui |= nuevo
        decidio |= nuevo
        frac_aqui[k] = va_aqui.mean()

    return {"t_arr": t_arr, "derivado": derivado, "frac_aqui": frac_aqui}
