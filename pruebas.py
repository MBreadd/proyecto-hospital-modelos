from entorno import generar_entorno
from social import decidir_llegadas
from hospital import simular_hospital


def probar_llegadas():
    entorno = generar_entorno(semilla=1)

    a = decidir_llegadas(entorno, beta=0)
    b = decidir_llegadas(entorno, beta=0)

    assert a == b, "Las llegadas deberían ser reproducibles"
    assert all(0 <= p["llegada"] < 360 for p in a)

    print("Prueba de llegadas: correcta")


def probar_hospital():
    entorno = generar_entorno(semilla=1)
    llegadas = decidir_llegadas(entorno, beta=3)
    resultado = simular_hospital(llegadas)

    assert resultado["atendidos"] <= resultado["llegadas"]
    assert resultado["pendientes"] >= 0
    assert resultado["espera_media"] >= 0

    print("Prueba del hospital: correcta")


if __name__ == "__main__":
    probar_llegadas()
    probar_hospital()
    print("Todas las pruebas terminaron correctamente.")