# Parámetros generales de la simulación

DURACION = 360          # minutos de simulación
PASO = 5                # minutos por intervalo
NUM_PERSONAS = 160

# Recursos iniciales del hospital
TRIAJES = 3
EQUIPOS = 14
CAMAS = 40

# Influencia social
BETA = 3

# Medidas adicionales
TIEMPO_ORIENTACION = 60
TIEMPO_REFUERZO = 90

# Tiempo medio de atención según gravedad:
# 0 = grave, 1 = moderado, 2 = leve
TIEMPO_ATENCION = [50, 30, 12]

# Tiempo adicional que una cama permanece ocupada
TIEMPO_ESTANCIA = [120, 40, 0]