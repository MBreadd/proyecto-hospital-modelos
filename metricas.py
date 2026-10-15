def calcular_metricas(resultado):
    return {
        "llegadas": resultado["llegadas"],
        "atendidos": resultado["atendidos"],
        "pendientes": resultado["pendientes"],
        "espera_media": resultado["espera_media"],
        "cola_maxima": resultado["cola_maxima"]
    }