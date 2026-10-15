"""
metricas.py  -  Indicadores de desempeño de UNA réplica de UN escenario.

Indicadores del proyecto: espera por gravedad, cola máxima, ocupación de camas y
pacientes pendientes al cierre. Se agregan: concentración de llegadas y
cumplimiento de metas de espera.

Nota sobre la espera: los pacientes que siguen esperando al minuto T tienen un dato
"censurado". Para no subestimar la espera se les asigna T - llegada (cota inferior).
"""
import numpy as np

from params import Params


def calcular_metricas(res: dict, prm: Params) -> dict:
    T = prm.T
    m = {}
    sismo = res["origen"] == 0
    sev = res["sev"][sismo]
    t_arr = res["t_arr"][sismo]
    t_ini = res["t_ini"][sismo]
    iniciada = ~np.isnan(t_ini)
    espera = np.where(iniciada, t_ini - t_arr, T - t_arr)

    m["llegadas_sismo"] = int(sismo.sum())
    m["derivados"] = res.get("n_derivados", 0)
    m["pendientes_sismo"] = int((~iniciada).sum())
    m["pendientes_total"] = int(np.isnan(res["t_ini"]).sum())

    for k in (1, 2, 3):
        sel = sev == k
        m[f"n_s{k}"] = int(sel.sum())
        m[f"espera_media_s{k}"] = float(espera[sel].mean()) if sel.any() else np.nan
        m[f"espera_p90_s{k}"] = float(np.percentile(espera[sel], 90)) if sel.any() else np.nan
        m[f"pct_fuera_meta_s{k}"] = float((espera[sel] > prm.metas_espera[k - 1]).mean() * 100) if sel.any() else np.nan
        m[f"pendientes_s{k}"] = int((sel & ~iniciada).sum())

    # Dónde se espera: cola de triaje vs. cola de atención (para identificar cuellos de botella)
    tri_ini, tri_fin = res["t_tri_ini"][sismo], res["t_tri_fin"][sismo]
    en_tri = ~np.isnan(tri_ini)
    m["espera_triaje_media"] = float((tri_ini[en_tri] - t_arr[en_tri]).mean()) if en_tri.any() else np.nan
    pasa = ~np.isnan(tri_fin) & iniciada
    m["espera_atencion_media"] = float((t_ini[pasa] - tri_fin[pasa]).mean()) if pasa.any() else np.nan

    m["cola_max"] = int(res["qmax_total"])
    m["cola_max_triaje"] = int(res["qmax_triaje"])
    m["cola_max_atencion"] = int(res["qmax_atencion"])
    m["ocup_camas_media"] = float(res["ocup_camas_media"])
    m["ocup_equipos_media"] = float(res["ocup_equipos_media"])
    mu = res["muestras"]
    c = res["cols_muestras"]
    m["ocup_camas_max"] = float((100.0 * mu[:, c.index("camas_ocup")] / mu[:, c.index("camas_cap")]).max())

    # Concentración de llegadas: máximo de pacientes en una ventana móvil de 60 min
    bins = np.arange(0, T + 10, 10)
    cuentas, _ = np.histogram(t_arr, bins=bins)
    ventana = np.convolve(cuentas, np.ones(6, dtype=int), mode="valid")
    m["pico_60min"] = int(ventana.max()) if len(ventana) else 0
    m["pct_en_pico_60"] = float(100.0 * ventana.max() / max(len(t_arr), 1))
    m["t_pico_min"] = float(bins[int(ventana.argmax())]) if len(ventana) else np.nan
    return m
