"""
params.py  -  Parámetros del modelo.

IMPORTANTE: todos los valores de este archivo son SUPUESTOS ACADÉMICOS ajustables.
No provienen de un hospital real. En la segunda mitad del proyecto se justifican
con literatura y se prueban con análisis de sensibilidad.

Convención de gravedad (triaje):  1 = crítico (rojo)
                                  2 = urgente (amarillo)
                                  3 = leve (verde)
Todos los tiempos están en MINUTOS.
"""
from dataclasses import dataclass


SEV_NOMBRES = {1: "Crítico (rojo)", 2: "Urgente (amarillo)", 3: "Leve (verde)"}


@dataclass(frozen=True)
class Params:
    # ------------------------------------------------------------------
    # Horizonte de simulación
    # ------------------------------------------------------------------
    T: float = 360.0            # 6 horas posteriores al sismo
    dt: float = 5.0             # paso del proceso de decisión social

    # ------------------------------------------------------------------
    # Población afectada y red social (quién influye en quién)
    # ------------------------------------------------------------------
    N: int = 160                # personas lesionadas que podrían acudir a ESTE hospital
    k_vecinos: int = 6          # contactos cercanos por persona (familiares/conocidos)
    p_rewire: float = 0.10      # red "mundo pequeño" (Watts-Strogatz)
    p_grav: tuple = (0.10, 0.30, 0.60)   # % crítico, urgente, leve

    # ------------------------------------------------------------------
    # Regla de decisión (comportamiento colectivo)
    #   h_i(t) = h_base[grav] * g(t) * (1 + beta * suscept[grav] * f_i(t))
    #   f_i(t) = fracción de contactos de i que ya decidieron venir a este hospital
    #   p_i    = 1 - exp(-h_i * dt)      (prob. de decidir en el intervalo)
    # beta = 0  ->  sin influencia social
    # ------------------------------------------------------------------
    t0_pico: float = 60.0                      # minuto del pico de la respuesta "natural"
    h_base: tuple = (0.025, 0.016, 0.0125)     # tasa base por minuto según gravedad
    suscept: tuple = (0.15, 0.60, 1.00)        # qué tanto influye el entorno según gravedad
    beta: float = 0.0                          # intensidad de la influencia social

    # ------------------------------------------------------------------
    # Hospital (recursos con capacidad limitada)
    # ------------------------------------------------------------------
    n_triaje: int = 3                    # enfermeras de triaje
    n_equipos: int = 14                  # equipos de atención (médico + enfermera)
    n_camas: int = 40                    # camas/espacios de atención
    camas_ocupadas_ini: int = 8          # pacientes que el hospital ya tenía
    estancia_ini_media: float = 120.0    # tiempo restante medio de esos pacientes

    tri_media: float = 2.0                       # duración media del triaje (gamma, forma 2)
    atencion_media: tuple = (50.0, 30.0, 12.0)   # atención activa (equipo ocupado) por gravedad
    estancia_extra_media: tuple = (120.0, 40.0, 0.0)  # tiempo extra en cama tras la atención
    cv_servicio: float = 0.6                     # variabilidad (lognormal) de los tiempos

    tasa_regular_h: float = 3.0                  # pacientes "habituales" por hora (no sismo)
    p_grav_regular: tuple = (0.05, 0.25, 0.70)

    # ------------------------------------------------------------------
    # Escenario 3: medidas de respuesta (None = no se aplica)
    # ------------------------------------------------------------------
    t_orient: float | None = None        # minuto en que empieza la orientación a la población
    efecto_orient: float = 0.60          # reducción de la influencia social tras orientar
    p_derivar: tuple = (0.0, 0.15, 0.35) # % que se deriva a otro establecimiento, por gravedad

    t_refuerzo: float | None = None      # minuto en que llega el refuerzo temporal
    extra_triaje: int = 1
    extra_equipos: int = 4
    extra_camas: int = 10

    # ------------------------------------------------------------------
    # Metas de espera ILUSTRATIVAS (min) para medir cumplimiento: crítico, urgente, leve
    # ------------------------------------------------------------------
    metas_espera: tuple = (10.0, 30.0, 90.0)
