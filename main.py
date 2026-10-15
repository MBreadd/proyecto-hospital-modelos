from experimentos import ejecutar_experimentos, resumir_resultados
from graficos import crear_graficos


def main():
    print("Simulación de saturación hospitalaria")
    print("Ejecutando escenarios...\n")

    datos = ejecutar_experimentos(replicas=100)
    resumen = resumir_resultados(datos)

    datos.to_csv("resultados_detallados.csv", index=False)
    resumen.to_csv("resumen_resultados.csv")

    print("RESULTADOS PROMEDIO")
    print(resumen)

    crear_graficos(resumen)

    print("\nArchivos generados:")
    print("- resultados_detallados.csv")
    print("- resumen_resultados.csv")
    print("- grafico_llegadas.png")
    print("- grafico_espera.png")
    print("- grafico_cola.png")


if __name__ == "__main__":
    main()