"""
entorno.py  -  Números aleatorios comunes (CRN: Common Random Numbers).

Idea: en cada réplica se sortea UNA SOLA VEZ la población, la red, las gravedades,
los tiempos de servicio y los números aleatorios de las decisiones. Los tres
escenarios reutilizan exactamente esos mismos números. Así, las diferencias entre
escenarios vienen de las reglas/medidas y no de la suerte del sorteo
("mantendremos iguales las demás condiciones").
"""
from dataclasses import dataclass

import networkx as nx
import numpy as np

from params import Params


def _lognormal(media, cv, z):
    """Lognormal con media y coef. de variación dados, usando normales estándar z."""
    media = np.asarray(media, dtype=float)
    sigma2 = np.log(1.0 + cv ** 2)
    mu = np.log(np.maximum(media, 1e-12)) - sigma2 / 2.0
    salida = np.exp(mu + np.sqrt(sigma2) * z)
    return np.where(media > 0, salida, 0.0)


@dataclass
class Entorno:
    # --- personas afectadas por el sismo
    sev: np.ndarray        # gravedad (1,2,3)
    adj: np.ndarray        # matriz de adyacencia de la red de contactos
    deg: np.ndarray        # grado (nº de contactos)
    U: np.ndarray          # uniformes para decidir "cuándo" (N x pasos)
    V: np.ndarray          # uniformes para decidir "derivación" (N x pasos)
    A: np.ndarray          # atención activa (min)
    O: np.ndarray          # estancia extra en cama (min)
    tri: np.ndarray        # duración del triaje (min)
    # --- pacientes habituales del hospital (no sismo)
    reg_t: np.ndarray
    reg_sev: np.ndarray
    reg_A: np.ndarray
    reg_O: np.ndarray
    reg_tri: np.ndarray
    # --- pacientes que ya estaban en cama al inicio: instante de alta
    ini_alta: np.ndarray


def generar_entorno(prm: Params, seed: int) -> Entorno:
    rng = np.random.default_rng(seed)
    N = prm.N

    G = nx.watts_strogatz_graph(N, prm.k_vecinos, prm.p_rewire,
                                seed=int(rng.integers(2 ** 31 - 1)))
    adj = nx.to_numpy_array(G, dtype=float)
    deg = np.maximum(adj.sum(axis=1), 1.0)

    sev = rng.choice([1, 2, 3], size=N, p=prm.p_grav)
    pasos = int(round(prm.T / prm.dt))
    U = rng.random((N, pasos))
    V = rng.random((N, pasos))

    A = _lognormal(np.array(prm.atencion_media)[sev - 1], prm.cv_servicio, rng.standard_normal(N))
    O = _lognormal(np.array(prm.estancia_extra_media)[sev - 1], prm.cv_servicio, rng.standard_normal(N))
    tri = rng.gamma(2.0, prm.tri_media / 2.0, size=N)

    # Pacientes habituales: llegan como proceso de Poisson durante todo el horizonte
    n_reg = int(rng.poisson(prm.tasa_regular_h * prm.T / 60.0))
    reg_t = np.sort(rng.uniform(0.0, prm.T, n_reg))
    reg_sev = rng.choice([1, 2, 3], size=n_reg, p=prm.p_grav_regular)
    reg_A = _lognormal(np.array(prm.atencion_media)[reg_sev - 1], prm.cv_servicio, rng.standard_normal(n_reg))
    reg_O = _lognormal(np.array(prm.estancia_extra_media)[reg_sev - 1], prm.cv_servicio, rng.standard_normal(n_reg))
    reg_tri = rng.gamma(2.0, prm.tri_media / 2.0, size=n_reg)

    ini_alta = rng.exponential(prm.estancia_ini_media, size=prm.camas_ocupadas_ini)

    return Entorno(sev, adj, deg, U, V, A, O, tri,
                   reg_t, reg_sev, reg_A, reg_O, reg_tri, ini_alta)
