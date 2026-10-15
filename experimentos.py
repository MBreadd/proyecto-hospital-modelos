"""
experimentos.py  -  Diseño de experimentos: escenarios, réplicas y estadística.

Escenarios (mismas condiciones salvo lo indicado):
    S1  llegadas SIN influencia social          (beta = 0)
    S2  llegadas CON influencia social          (beta > 0)
    S3  S2 + orientación a la población (t_orient) + refuerzo temporal (t_refuerzo)

Se usan números aleatorios comunes (CRN): cada réplica r comparte semilla entre
escenarios, por lo que las comparaciones S2-S1 y S3-S2 son PAREADAS.
"""
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy import stats

from entorno import generar_entorno
from hospital import simular_hospital
from metricas import calcular_metricas
from params import Params
from social import decidir_llegadas

BETA_DEFECTO = 3.0
T_ORIENT = 60.0      # minuto en que empieza la orientación a la población
T_REFUERZO = 90.0    # minuto en que llega el refuerzo temporal

NOMBRES = {
    "S1": "S1 Sin influencia social",  # (nombres para gráficos y tablas)
    "S2": "S2 Con influencia social",
    "S3": "S3 Influencia + medidas",
}


def definir_escenarios(base: Params, beta: float = BETA_DEFECTO) -> dict:
    return {
        "S1": replace(base, beta=0.0),
        "S2": replace(base, beta=beta),
        "S3": replace(base, beta=beta, t_orient=T_ORIENT, t_refuerzo=T_REFUERZO),
    }


def _series_de(res: dict, prm: Params) -> dict:
    """Series de tiempo de una réplica: llegadas cada 10 min, cola total y ocupación de camas."""
    sismo = res["origen"] == 0
    bins = np.arange(0, prm.T + 10, 10)
    llegadas, _ = np.histogram(res["t_arr"][sismo], bins=bins)
    mu, c = res["muestras"], res["cols_muestras"]
    cola = mu[:, c.index("q_triaje")] + mu[:, c.index("q_atencion")]
    camas = 100.0 * mu[:, c.index("camas_ocup")] / mu[:, c.index("camas_cap")]
    return {"llegadas": llegadas, "cola": cola, "camas": camas, "t_muestra": mu[:, 0]}


def correr(base: Params, reps: int = 200, beta: float = BETA_DEFECTO, semilla0: int = 1000):
    esc = definir_escenarios(base, beta)
    filas = []
    series = {k: {"llegadas": [], "cola": [], "camas": []} for k in esc}
    t_muestra = None
    for r in range(reps):
        env = generar_entorno(base, semilla0 + r)
        for k, prm in esc.items():
            ll = decidir_llegadas(env, prm)
            res = simular_hospital(env, ll, prm)
            m = calcular_metricas(res, prm)
            m.update(escenario=k, rep=r)
            filas.append(m)
            s = _series_de(res, prm)
            t_muestra = s["t_muestra"]
            for nombre in ("llegadas", "cola", "camas"):
                series[k][nombre].append(s[nombre])
    df = pd.DataFrame(filas)
    series = {k: {n: np.array(v) for n, v in d.items()} for k, d in series.items()}
    series["t_muestra"] = t_muestra
    return df, series


def _ic95(x: np.ndarray):
    x = np.asarray(x, dtype=float)
    n = len(x)
    media = x.mean()
    if n < 2:
        return media, np.nan
    mitad = stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n)
    return media, mitad


METRICAS_CLAVE = [
    "llegadas_sismo", "derivados", "pct_en_pico_60", "cola_max",
    "espera_media_s1", "espera_media_s2", "espera_media_s3",
    "espera_p90_s3", "pct_fuera_meta_s2", "pct_fuera_meta_s3",
    "ocup_camas_media", "ocup_camas_max", "ocup_equipos_media",
    "pendientes_sismo", "pendientes_total",
]


def resumen(df: pd.DataFrame, metricas=METRICAS_CLAVE) -> pd.DataFrame:
    filas = []
    for esc, g in df.groupby("escenario"):
        for met in metricas:
            media, mitad = _ic95(g[met])
            filas.append({"escenario": esc, "metrica": met, "media": media, "ic95_mitad": mitad})
    return pd.DataFrame(filas)


def diferencias_pareadas(df: pd.DataFrame, a: str, b: str, metricas=METRICAS_CLAVE) -> pd.DataFrame:
    """Diferencia (b - a) por réplica, con IC 95 % (t pareada, gracias a CRN)."""
    da = df[df.escenario == a].sort_values("rep")
    db = df[df.escenario == b].sort_values("rep")
    filas = []
    for met in metricas:
        dif = db[met].to_numpy() - da[met].to_numpy()
        media, mitad = _ic95(dif)
        filas.append({"comparacion": f"{b} - {a}", "metrica": met, "dif_media": media,
                      "ic95_mitad": mitad, "significativa": abs(media) > mitad if not np.isnan(mitad) else False})
    return pd.DataFrame(filas)


def ablacion_medidas(base: Params, beta: float = BETA_DEFECTO, reps: int = 100, semilla0: int = 1000) -> pd.DataFrame:
    """¿Cuál medida aporta más? Se prueban por separado la orientación y el refuerzo (sobre S2)."""
    variantes = {
        "Sin medidas (S2)": replace(base, beta=beta),
        "Solo orientación": replace(base, beta=beta, t_orient=T_ORIENT),
        "Solo refuerzo": replace(base, beta=beta, t_refuerzo=T_REFUERZO),
        "Orientación + refuerzo (S3)": replace(base, beta=beta, t_orient=T_ORIENT, t_refuerzo=T_REFUERZO),
    }
    filas = []
    for r in range(reps):
        env = generar_entorno(base, semilla0 + r)
        for nombre, prm in variantes.items():
            res = simular_hospital(env, decidir_llegadas(env, prm), prm)
            m = calcular_metricas(res, prm)
            m.update(variante=nombre, rep=r)
            filas.append(m)
    return pd.DataFrame(filas)


def descomposicion_volumen(base: Params, beta: float = BETA_DEFECTO, reps: int = 100, semilla0: int = 1000) -> pd.DataFrame:
    """
    ¿El empeoramiento por influencia social se debe a que llegan MÁS personas (volumen)
    o a que llegan MÁS JUNTAS (concentración)?
    Truco con CRN: en S2 "volumen igualado" solo se dejan llegar las personas que también
    llegan en S1, pero con los tiempos de llegada de S2 (más tempranos y concentrados).
    """
    p1, p2 = replace(base, beta=0.0), replace(base, beta=beta)
    filas = []
    for r in range(reps):
        env = generar_entorno(base, semilla0 + r)
        l1, l2 = decidir_llegadas(env, p1), decidir_llegadas(env, p2)
        l2m = dict(l2, t_arr=np.where(~np.isnan(l1["t_arr"]), l2["t_arr"], np.nan))
        for nombre, prm, ll in (("S1 sin influencia", p1, l1),
                                ("S2 con volumen igualado a S1", p2, l2m),
                                ("S2 con influencia", p2, l2)):
            m = calcular_metricas(simular_hospital(env, ll, prm), prm)
            m.update(variante=nombre, rep=r)
            filas.append(m)
    return pd.DataFrame(filas)


def barrido_beta(base: Params, betas=(0, 1, 2, 3, 4, 6), reps: int = 100, semilla0: int = 1000) -> pd.DataFrame:
    """Sensibilidad al nivel de influencia social (sin medidas de respuesta)."""
    filas = []
    for r in range(reps):
        env = generar_entorno(base, semilla0 + r)
        for b in betas:
            prm = replace(base, beta=float(b))
            res = simular_hospital(env, decidir_llegadas(env, prm), prm)
            m = calcular_metricas(res, prm)
            m.update(beta=float(b), rep=r)
            filas.append(m)
    return pd.DataFrame(filas)
