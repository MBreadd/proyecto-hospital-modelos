"""
pruebas.py  -  Verificación del código (invariantes del modelo).
Ejecutar:  python pruebas.py
Si algo falla, lanza AssertionError indicando qué regla se rompió.
"""
from dataclasses import replace

import numpy as np

from entorno import generar_entorno
from experimentos import definir_escenarios
from hospital import simular_hospital
from params import Params
from social import decidir_llegadas


def probar_una_replica(semilla: int):
    base = Params()
    env = generar_entorno(base, semilla)
    for nombre, prm in definir_escenarios(base).items():
        ll = decidir_llegadas(env, prm)
        res = simular_hospital(env, ll, prm)
        n = len(res["t_arr"])
        t_ini, t_alta, t_tri_fin = res["t_ini"], res["t_alta"], res["t_tri_fin"]

        # 1) Conservación: nadie "se pierde" ni se atiende antes de llegar
        assert np.all(res["t_arr"] <= prm.T), "hay llegadas fuera del horizonte"
        ok = ~np.isnan(t_ini)
        assert np.all(t_ini[ok] >= t_tri_fin[ok] - 1e-9), f"{nombre}: atención antes de terminar triaje"
        assert np.all(t_tri_fin[ok] >= res["t_arr"][ok] - 1e-9), f"{nombre}: triaje antes de llegar"
        sale = ~np.isnan(t_alta)
        assert np.all(~sale | ok), f"{nombre}: alta sin haber sido atendido"
        pendientes = int(np.isnan(t_ini).sum())
        atendidos = int(ok.sum())
        assert pendientes + atendidos == n, f"{nombre}: la suma de pacientes no cuadra"

        # 2) Capacidad: nunca se supera lo disponible
        mu, c = res["muestras"], res["cols_muestras"]
        assert np.all(mu[:, c.index("camas_ocup")] <= mu[:, c.index("camas_cap")]), f"{nombre}: camas excedidas"
        assert np.all(mu[:, c.index("equipos_ocup")] <= mu[:, c.index("equipos_cap")]), f"{nombre}: equipos excedidos"

        # 3) Prioridad: si alguien empieza a ser atendido en t, no puede haber alguien MÁS GRAVE
        #    ya con triaje terminado y todavía esperando en ese mismo instante.
        sev = res["sev"]
        for i in np.where(ok)[0]:
            esperando_mas_grave = (sev < sev[i]) & (t_tri_fin <= t_ini[i] - 1e-9) & \
                                  (np.isnan(t_ini) | (t_ini > t_ini[i] + 1e-9))
            assert not esperando_mas_grave.any(), f"{nombre}: se violó la prioridad por gravedad"
    return True


def probar_crn():
    """Con beta = 0 y mismo entorno, el resultado debe repetirse exactamente (reproducibilidad)."""
    base = Params()
    env = generar_entorno(base, 7)
    prm = replace(base, beta=0.0)
    a = decidir_llegadas(env, prm)["t_arr"]
    b = decidir_llegadas(env, prm)["t_arr"]
    assert np.array_equal(a, b, equal_nan=True), "no es reproducible con la misma semilla"


def probar_influencia_adelanta():
    """Con más influencia social, deben llegar más personas y más temprano (en promedio)."""
    base = Params()
    n1 = n2 = 0
    for s in range(30):
        env = generar_entorno(base, s)
        n1 += np.sum(~np.isnan(decidir_llegadas(env, replace(base, beta=0.0))["t_arr"]))
        n2 += np.sum(~np.isnan(decidir_llegadas(env, replace(base, beta=3.0))["t_arr"]))
    assert n2 > n1, "la influencia social debería aumentar las llegadas dentro del horizonte"


if __name__ == "__main__":
    for s in range(10):
        probar_una_replica(s)
    probar_crn()
    probar_influencia_adelanta()
    print("OK: todas las pruebas pasaron (conservación, capacidad, prioridad, reproducibilidad, influencia).")
