"""
graficos.py  -  Figuras del avance (leen la carpeta resultados/ creada por main.py).
Uso:  python graficos.py
Paleta: categórica de 3 colores validada (azul, naranja, aqua) -> un color fijo por escenario.
"""
import os
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from params import Params

COL = {"S1": "#2a78d6", "S2": "#eb6834", "S3": "#1baf7a"}
ETQ = {"S1": "S1 Sin influencia social", "S2": "S2 Con influencia social", "S3": "S3 Influencia + medidas"}
TINTA, TINTA2, MUDO, GRILLA, BASE, FONDO = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
GRIS_A, GRIS_B = "#898781", "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
    "font.size": 10, "axes.edgecolor": BASE, "axes.labelcolor": TINTA2,
    "xtick.color": MUDO, "ytick.color": MUDO, "text.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRILLA, "grid.linewidth": 0.8, "axes.axisbelow": True,
})


def _ic(x):
    x = np.asarray(x, float)
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


def _guardar(fig, ruta):
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  ->", ruta)


def fig_llegadas(series, out):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    x = np.arange(0, 360, 10) + 5
    # S3 se dibuja debajo de S2: hasta la orientación (min 60) ambos usan los mismos números aleatorios
    for k, lw in (("S1", 2), ("S3", 3.2), ("S2", 2)):
        y = series[k]["llegadas"].mean(axis=0)
        ax.plot(x / 60, y, color=COL[k], lw=lw, label=ETQ[k])
    h, l = ax.get_legend_handles_labels()
    orden = [l.index(ETQ[k]) for k in ("S1", "S2", "S3")]
    ax.axvline(1.0, color=MUDO, lw=1, ls=(0, (2, 3)))
    ax.text(1.04, ax.get_ylim()[1] * 0.97, "min 60: empieza la\norientación (solo S3)", fontsize=8, color=TINTA2, va="top")
    ax.set_xlabel("Horas desde el sismo")
    ax.set_ylabel("Pacientes por sismo que llegan\n(cada 10 min, promedio de réplicas)")
    ax.set_title("Con influencia social las llegadas se concentran y se adelantan", loc="left", color=TINTA)
    ax.legend([h[i] for i in orden], [l[i] for i in orden], frameon=False, loc="upper right")
    ax.set_xlim(0, 6)
    _guardar(fig, f"{out}/fig1_llegadas.png")


def fig_cola(series, out):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    t = series["t_muestra"] / 60
    for k in ("S1", "S2", "S3"):
        m = series[k]["cola"]
        ax.plot(t, m.mean(axis=0), color=COL[k], lw=2, label=ETQ[k])
        ax.fill_between(t, np.percentile(m, 10, axis=0), np.percentile(m, 90, axis=0),
                        color=COL[k], alpha=0.12, lw=0)
    ax.set_xlabel("Horas desde el sismo")
    ax.set_ylabel("Pacientes esperando\n(triaje + atención; media y banda 10-90 %)")
    ax.set_title("La cola crece más y tarda más en vaciarse con influencia social", loc="left", color=TINTA)
    ax.legend(frameon=False, loc="upper right")
    ax.set_xlim(0, 6)
    ax.set_ylim(bottom=0)
    _guardar(fig, f"{out}/fig2_cola.png")


def fig_espera(df, out, prm):
    fig, axs = plt.subplots(1, 3, figsize=(9.5, 4.0))
    nombres = {1: "Crítico (rojo)", 2: "Urgente (amarillo)", 3: "Leve (verde)"}
    for sev, ax in zip((1, 2, 3), axs):
        for i, k in enumerate(("S1", "S2", "S3")):
            v = df[df.escenario == k][f"espera_media_s{sev}"]
            ax.bar(i, v.mean(), width=0.72, color=COL[k], yerr=_ic(v),
                   error_kw={"ecolor": TINTA2, "lw": 1, "capsize": 3})
            ax.text(i, v.mean() + _ic(v), f"{v.mean():.0f}", ha="center", va="bottom", fontsize=9, color=TINTA2,
                    bbox=dict(fc=FONDO, ec="none", pad=0.8))
        ax.axhline(prm.metas_espera[sev - 1], color=TINTA2, lw=1, ls=(0, (4, 3)), zorder=0.5)
        ax.set_title(nombres[sev], fontsize=10, color=TINTA)
        ax.set_xticks([0, 1, 2], ["S1", "S2", "S3"])
        ax.grid(axis="x", visible=False)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    axs[0].set_ylabel("Espera media hasta ser atendido (min)")
    fig.suptitle("Espera según gravedad (media e IC 95 %; línea punteada = meta ilustrativa; cada panel con su escala)",
                 x=0.01, ha="left", fontsize=11, color=TINTA)
    fig.tight_layout()
    _guardar(fig, f"{out}/fig3_espera_gravedad.png")


def fig_camas(series, out):
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    t = series["t_muestra"] / 60
    for k in ("S1", "S2", "S3"):
        ax.plot(t, series[k]["camas"].mean(axis=0), color=COL[k], lw=2, label=ETQ[k])
    ax.set_xlabel("Horas desde el sismo")
    ax.set_ylabel("Ocupación de camas (%)")
    ax.set_title("Las camas se acercan a su límite en el pico", loc="left", color=TINTA)
    ax.legend(frameon=False, loc="lower right")
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 105)
    _guardar(fig, f"{out}/fig4_camas.png")


def fig_barrido(bar, out):
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 3.9))
    betas = sorted(bar.beta.unique())
    for ax, met, tit in ((axs[0], "pct_en_pico_60", "% de llegadas en la hora más cargada"),
                         (axs[1], "cola_max", "Cola máxima (pacientes)")):
        medias = [bar[bar.beta == b][met].mean() for b in betas]
        ics = [_ic(bar[bar.beta == b][met]) for b in betas]
        ax.errorbar(betas, medias, yerr=ics, color=COL["S2"], lw=2, marker="o", ms=6,
                    mfc=COL["S2"], mec=FONDO, mew=1.5, ecolor=TINTA2, capsize=3, elinewidth=1)
        ax.set_xlabel("Intensidad de la influencia social (β)")
        ax.set_title(tit, loc="left", fontsize=10, color=TINTA)
        ax.set_ylim(bottom=0)
    fig.suptitle("Más influencia social = llegadas más concentradas y colas más largas (β = 0 es S1)",
                 x=0.01, ha="left", fontsize=11, color=TINTA)
    fig.tight_layout()
    _guardar(fig, f"{out}/fig5_barrido_beta.png")


def fig_volumen(des, out):
    orden = ["S1 sin influencia", "S2 con volumen igualado a S1", "S2 con influencia"]
    etiqueta = ["S1\nsin influencia", "S2 con el mismo\nnº de pacientes que S1", "S2\ncon influencia"]
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 4.0))
    for ax, met, tit in ((axs[0], "cola_max", "Cola máxima (pacientes)"),
                         (axs[1], "espera_media_s2", "Espera media de urgentes (min)")):
        for i, v in enumerate(orden):
            serie = des[des.variante == v][met]
            color = COL["S1"] if i == 0 else COL["S2"]
            ax.bar(i, serie.mean(), width=0.7, color=color, yerr=_ic(serie), hatch="///" if i == 1 else None,
                   edgecolor=FONDO if i != 1 else "#ffffff", linewidth=0,
                   error_kw={"ecolor": TINTA2, "lw": 1, "capsize": 3})
            ax.text(i, serie.mean() + _ic(serie), f"{serie.mean():.0f}", ha="center", va="bottom", fontsize=9, color=TINTA2)
        ax.set_xticks(range(3), etiqueta, fontsize=8.5)
        ax.set_title(tit, loc="left", fontsize=10, color=TINTA)
        ax.grid(axis="x", visible=False)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    fig.suptitle("Gran parte del empeoramiento viene de que llegan juntos, no solo de que llegan más",
                 x=0.01, ha="left", fontsize=11, color=TINTA)
    fig.tight_layout()
    _guardar(fig, f"{out}/fig6_volumen_vs_concentracion.png")


def fig_ablacion(abl, out):
    orden = ["Sin medidas (S2)", "Solo orientación", "Solo refuerzo", "Orientación + refuerzo (S3)"]
    etiqueta = ["Sin medidas\n(S2)", "Solo\norientación", "Solo\nrefuerzo", "Ambas\n(S3)"]
    colores = [COL["S2"], GRIS_A, GRIS_B, COL["S3"]]
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 4.0))
    for ax, met, tit in ((axs[0], "cola_max", "Cola máxima (pacientes)"),
                         (axs[1], "espera_media_s2", "Espera media de urgentes (min)")):
        for i, v in enumerate(orden):
            serie = abl[abl.variante == v][met]
            ax.bar(i, serie.mean(), width=0.7, color=colores[i], yerr=_ic(serie),
                   error_kw={"ecolor": TINTA2, "lw": 1, "capsize": 3})
            ax.text(i, serie.mean() + _ic(serie), f"{serie.mean():.0f}", ha="center", va="bottom", fontsize=9, color=TINTA2)
        ax.set_xticks(range(4), etiqueta, fontsize=8.5)
        ax.set_title(tit, loc="left", fontsize=10, color=TINTA)
        ax.grid(axis="x", visible=False)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    fig.suptitle("Cada medida ayuda por separado; juntas ayudan más (orientación a partir del min 60, refuerzo desde el min 90)",
                 x=0.01, ha="left", fontsize=10.5, color=TINTA)
    fig.tight_layout()
    _guardar(fig, f"{out}/fig7_ablacion_medidas.png")


def main(carpeta="resultados"):
    out = f"{carpeta}/figuras"
    os.makedirs(out, exist_ok=True)
    with open(f"{carpeta}/series.pkl", "rb") as f:
        series = pickle.load(f)
    df = pd.read_csv(f"{carpeta}/metricas_por_replica.csv")
    bar = pd.read_csv(f"{carpeta}/barrido_beta.csv")
    abl = pd.read_csv(f"{carpeta}/ablacion_medidas.csv")
    des = pd.read_csv(f"{carpeta}/descomposicion_volumen.csv")
    prm = Params()
    print("Generando figuras ...")
    fig_llegadas(series, out)
    fig_cola(series, out)
    fig_espera(df, out, prm)
    fig_camas(series, out)
    fig_barrido(bar, out)
    fig_volumen(des, out)
    fig_ablacion(abl, out)


if __name__ == "__main__":
    main()
