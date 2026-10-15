"""
main.py  -  Corre los 3 escenarios, el barrido de influencia social y guarda resultados.

Uso:
    python main.py                 # 200 réplicas por escenario (≈ 1-2 min)
    python main.py --reps 30       # prueba rápida
Salida: carpeta resultados/ (CSV + series.npz). Luego:  python graficos.py
"""
import argparse
import os
import pickle

import pandas as pd

from experimentos import (BETA_DEFECTO, ablacion_medidas, barrido_beta, correr, descomposicion_volumen,
                          diferencias_pareadas, resumen)
from params import Params


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200, help="réplicas por escenario")
    ap.add_argument("--beta", type=float, default=BETA_DEFECTO, help="intensidad de influencia social en S2 y S3")
    ap.add_argument("--reps-barrido", type=int, default=100, help="réplicas por valor de beta en el barrido")
    ap.add_argument("--salida", default="resultados")
    a = ap.parse_args()

    os.makedirs(a.salida, exist_ok=True)
    base = Params()

    print(f"Corriendo {a.reps} réplicas x 3 escenarios (beta={a.beta}) ...")
    df, series = correr(base, reps=a.reps, beta=a.beta)
    df.to_csv(f"{a.salida}/metricas_por_replica.csv", index=False)
    with open(f"{a.salida}/series.pkl", "wb") as f:
        pickle.dump(series, f)

    res = resumen(df)
    res.to_csv(f"{a.salida}/resumen.csv", index=False)
    dif = pd.concat([diferencias_pareadas(df, "S1", "S2"), diferencias_pareadas(df, "S2", "S3")])
    dif.to_csv(f"{a.salida}/diferencias_pareadas.csv", index=False)

    print(f"Barrido de beta ({a.reps_barrido} réplicas por valor) ...")
    bar = barrido_beta(base, reps=a.reps_barrido)
    bar.to_csv(f"{a.salida}/barrido_beta.csv", index=False)

    print("Ablación de medidas (orientación vs refuerzo) ...")
    abl = ablacion_medidas(base, beta=a.beta, reps=a.reps_barrido)
    abl.to_csv(f"{a.salida}/ablacion_medidas.csv", index=False)

    print("Descomposición volumen vs concentración ...")
    des = descomposicion_volumen(base, beta=a.beta, reps=a.reps_barrido)
    des.to_csv(f"{a.salida}/descomposicion_volumen.csv", index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)
    tabla = res.pivot(index="metrica", columns="escenario", values="media").round(2)
    print("\n=== Medias por escenario ===")
    print(tabla)
    print("\n=== Diferencias pareadas (IC 95 %) ===")
    print(dif.round(2).to_string(index=False))
    print("\n=== Ablación de medidas (medias) ===")
    cols = ["espera_media_s1", "espera_media_s2", "espera_media_s3", "cola_max", "pendientes_sismo", "derivados"]
    print(abl.groupby("variante")[cols].mean().round(1))
    print("\n=== Volumen vs concentración (medias) ===")
    cols2 = ["llegadas_sismo", "pct_en_pico_60", "espera_media_s1", "espera_media_s2", "espera_media_s3", "cola_max"]
    print(des.groupby("variante")[cols2].mean().round(1))


if __name__ == "__main__":
    main()
