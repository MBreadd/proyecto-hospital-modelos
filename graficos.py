import matplotlib.pyplot as plt


def crear_graficos(resumen):
    # Gráfico 1: llegadas
    resumen["llegadas"].plot(kind="bar")
    plt.title("Promedio de llegadas por escenario")
    plt.ylabel("Pacientes")
    plt.xlabel("Escenario")
    plt.tight_layout()
    plt.savefig("grafico_llegadas.png")
    plt.close()

    # Gráfico 2: espera media
    resumen["espera_media"].plot(kind="bar")
    plt.title("Tiempo medio de espera")
    plt.ylabel("Minutos")
    plt.xlabel("Escenario")
    plt.tight_layout()
    plt.savefig("grafico_espera.png")
    plt.close()

    # Gráfico 3: cola máxima
    resumen["cola_maxima"].plot(kind="bar")
    plt.title("Cola máxima observada")
    plt.ylabel("Pacientes")
    plt.xlabel("Escenario")
    plt.tight_layout()
    plt.savefig("grafico_cola.png")
    plt.close()