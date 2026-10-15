"""
validacion_mmc.py  -  Validación del MOTOR de eventos discretos contra teoría.

Se configura el motor como una cola M/M/c clásica (llegadas Poisson, atención
exponencial, c servidores, sin triaje ni límite de camas) y se compara la espera media
en cola simulada con la fórmula analítica de Erlang C.
Si el motor está bien programado, ambos números deben ser muy parecidos.

Ejecutar:  python validacion_mmc.py
"""
from dataclasses import replace
from math import factorial

import numpy as np

from hospital import simular_core
from params import Params


def espera_teorica_erlang_c(lam: float, mu: float, c: int) -> float:
    a = lam / mu
    rho = a / c
    suma = sum(a ** k / factorial(k) for k in range(c))
    cola = a ** c / (factorial(c) * (1 - rho))
    p_espera = cola / (suma + cola)           # probabilidad de esperar (Erlang C)
    return p_espera / (c * mu - lam)           # Wq


def simular_mmc(lam=0.24, mu=0.10, c=3, T=200_000.0, semilla=1, calentamiento=0.05):
    rng = np.random.default_rng(semilla)
    n = rng.poisson(lam * T)
    t_arr = np.sort(rng.uniform(0, T, n))
    A = rng.exponential(1.0 / mu, n)
    prm = replace(Params(), T=T, n_triaje=10_000, n_equipos=c, n_camas=10_000,
                  camas_ocupadas_ini=0, t_refuerzo=None)
    res = simular_core(t_arr, np.full(n, 3), A, np.zeros(n), np.zeros(n),
                       np.zeros(n, dtype=int), np.array([]), prm, paso_muestra=1000.0)
    ok = ~np.isnan(res["t_ini"]) & (t_arr > calentamiento * T)
    return float((res["t_ini"][ok] - t_arr[ok]).mean())


if __name__ == "__main__":
    lam, mu, c = 0.24, 0.10, 3          # rho = 0.8
    teorico = espera_teorica_erlang_c(lam, mu, c)
    sims = [simular_mmc(lam, mu, c, semilla=s) for s in range(10, 20)]
    media = float(np.mean(sims))
    ee = float(np.std(sims, ddof=1) / np.sqrt(len(sims)))      # error estándar de la media
    print(f"M/M/{c}  lambda={lam}/min  mu={mu}/min  rho={lam / (c * mu):.2f}")
    print(f"Espera media en cola TEÓRICA (Erlang C): {teorico:.2f} min")
    print(f"Espera media en cola SIMULADA ({len(sims)} corridas): {media:.2f} min  (error estándar {ee:.2f})")
    print(f"Error relativo: {abs(media - teorico) / teorico * 100:.1f} %")
    dentro = abs(media - teorico) <= 2 * ee
    print("Conclusión:", "la teoría cae dentro de ±2 errores estándar -> motor validado" if dentro
          else "la teoría queda fuera de ±2 errores estándar -> revisar el motor")
