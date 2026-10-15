"""
hospital.py  -  Simulación de eventos discretos (DES) del hospital.

Flujo de cada paciente:
    llegada -> cola de triaje -> triaje -> cola de atención (por prioridad de gravedad)
            -> atención (ocupa 1 equipo + 1 cama) -> fin de atención (libera el equipo)
            -> fin de estancia (libera la cama) -> salida

Eventos:  ARR, TRI_END, END_ACT, END_STAY, CAP (refuerzo), SAMPLE (muestreo), INI_REL
El reloj salta de evento en evento usando una cola de prioridad (heapq).
Regla de prioridad: primero la gravedad (1 antes que 2 antes que 3) y, a igual
gravedad, el que terminó antes el triaje.
"""
import heapq
import itertools
from collections import deque

import numpy as np

from entorno import Entorno
from params import Params

ARR, TRI_END, END_ACT, END_STAY, CAP, SAMPLE, INI_REL = range(7)


def simular_core(t_arr, sev, A, O, tri, origen, ini_alta, prm: Params, paso_muestra: float = 5.0) -> dict:
    """Motor DES. Recibe vectores de pacientes (un elemento por paciente)."""
    T = prm.T
    n = len(t_arr)

    t_tri_ini = np.full(n, np.nan)
    t_tri_fin = np.full(n, np.nan)
    t_ini = np.full(n, np.nan)       # inicio de la atención
    t_alta = np.full(n, np.nan)      # salida de la cama

    # --- estado del sistema
    cap_triaje, cap_equipos, cap_camas = prm.n_triaje, prm.n_equipos, prm.n_camas
    tri_ocup = eq_ocup = 0
    camas_ocup = len(ini_alta)
    cola_triaje = deque()
    cola_trat = []                   # heap de (gravedad, instante fin triaje, id)

    heap: list = []
    cnt = itertools.count()

    def push(t, tipo, pid=-1):
        heapq.heappush(heap, (t, next(cnt), tipo, pid))

    # --- eventos iniciales
    for pid in range(n):
        if t_arr[pid] <= T:
            push(t_arr[pid], ARR, pid)
    for t_alta_ini in ini_alta:
        push(t_alta_ini, INI_REL)
    if prm.t_refuerzo is not None:
        push(prm.t_refuerzo, CAP)
    t_m = 0.0
    while t_m <= T + 1e-9:
        push(t_m, SAMPLE)
        t_m += paso_muestra

    # --- acumuladores
    t_last = 0.0
    area_camas = area_cap_camas = area_eq = area_cap_eq = 0.0
    qmax_total = qmax_trat = qmax_tri = 0
    n_llegadas = 0
    muestras = []

    def intentar_triaje(t):
        nonlocal tri_ocup
        while tri_ocup < cap_triaje and cola_triaje:
            pid = cola_triaje.popleft()
            tri_ocup += 1
            t_tri_ini[pid] = t
            push(t + tri[pid], TRI_END, pid)

    def intentar_atencion(t):
        nonlocal eq_ocup, camas_ocup
        while cola_trat and eq_ocup < cap_equipos and camas_ocup < cap_camas:
            _, _, pid = heapq.heappop(cola_trat)
            eq_ocup += 1
            camas_ocup += 1
            t_ini[pid] = t
            push(t + A[pid], END_ACT, pid)
            push(t + A[pid] + O[pid], END_STAY, pid)

    while heap:
        t, _, tipo, pid = heapq.heappop(heap)
        if t > T:
            break
        d = t - t_last
        area_camas += camas_ocup * d
        area_cap_camas += cap_camas * d
        area_eq += eq_ocup * d
        area_cap_eq += cap_equipos * d
        t_last = t

        if tipo == ARR:
            n_llegadas += 1
            cola_triaje.append(pid)
            intentar_triaje(t)
        elif tipo == TRI_END:
            tri_ocup -= 1
            t_tri_fin[pid] = t
            heapq.heappush(cola_trat, (int(sev[pid]), t, pid))
            intentar_triaje(t)
            intentar_atencion(t)
        elif tipo == END_ACT:
            eq_ocup -= 1
            intentar_atencion(t)
        elif tipo == END_STAY:
            camas_ocup -= 1
            t_alta[pid] = t
            intentar_atencion(t)
        elif tipo == INI_REL:
            camas_ocup -= 1
            intentar_atencion(t)
        elif tipo == CAP:
            cap_triaje += prm.extra_triaje
            cap_equipos += prm.extra_equipos
            cap_camas += prm.extra_camas
            intentar_triaje(t)
            intentar_atencion(t)
        elif tipo == SAMPLE:
            por_sev = np.bincount([s for s, _, _ in cola_trat], minlength=4)[1:]
            muestras.append((t, len(cola_triaje), len(cola_trat), *por_sev,
                             camas_ocup, cap_camas, eq_ocup, cap_equipos, n_llegadas))

        qmax_total = max(qmax_total, len(cola_triaje) + len(cola_trat))
        qmax_trat = max(qmax_trat, len(cola_trat))
        qmax_tri = max(qmax_tri, len(cola_triaje))

    d = T - t_last
    area_camas += camas_ocup * d
    area_cap_camas += cap_camas * d
    area_eq += eq_ocup * d
    area_cap_eq += cap_equipos * d

    cols = ["t", "q_triaje", "q_atencion", "q_s1", "q_s2", "q_s3",
            "camas_ocup", "camas_cap", "equipos_ocup", "equipos_cap", "llegadas_acum"]
    return {
        "t_arr": np.asarray(t_arr), "sev": np.asarray(sev), "origen": np.asarray(origen),
        "t_tri_ini": t_tri_ini, "t_tri_fin": t_tri_fin, "t_ini": t_ini, "t_alta": t_alta,
        "muestras": np.array(muestras), "cols_muestras": cols,
        "qmax_total": qmax_total, "qmax_atencion": qmax_trat, "qmax_triaje": qmax_tri,
        "ocup_camas_media": 100.0 * area_camas / max(area_cap_camas, 1e-9),
        "ocup_equipos_media": 100.0 * area_eq / max(area_cap_eq, 1e-9),
    }


def simular_hospital(env: Entorno, llegadas: dict, prm: Params) -> dict:
    """Arma la lista de pacientes (sismo + habituales) y corre el motor DES."""
    ts = llegadas["t_arr"]
    idx = np.where(~np.isnan(ts) & (ts <= prm.T))[0]

    t_arr = np.concatenate([ts[idx], env.reg_t])
    sev = np.concatenate([env.sev[idx], env.reg_sev])
    A = np.concatenate([env.A[idx], env.reg_A])
    O = np.concatenate([env.O[idx], env.reg_O])
    tri = np.concatenate([env.tri[idx], env.reg_tri])
    origen = np.concatenate([np.zeros(len(idx), dtype=int), np.ones(len(env.reg_t), dtype=int)])

    res = simular_core(t_arr, sev, A, O, tri, origen, env.ini_alta, prm)
    res["n_derivados"] = int(llegadas["derivado"].sum())
    return res
