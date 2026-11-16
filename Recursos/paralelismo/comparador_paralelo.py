import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..algoritmo_base import costo_asignacion
from ..modelos import Actividad, Recurso
from ..planificacion import Asignacion, Planificacion
from ..reglas import MotorReglas, habilidades


def obtener_maximo_procesos() -> int:
    cantidad = os.cpu_count()

    if cantidad is None:
        return 1

    return cantidad


def validar_cantidad(cantidad: int) -> None:
    if not isinstance(cantidad, int) or cantidad < 1:
        raise ValueError("La cantidad de evaluaciones debe ser un entero mayor o igual a 1.")


def validar_procesos(procesos: int) -> None:
    maximo = obtener_maximo_procesos()

    if not isinstance(procesos, int) or procesos < 1 or procesos > maximo:
        raise ValueError(f"La cantidad de procesos debe ser un entero entre 1 y {maximo}.")


def validar_semilla(semilla: int) -> None:
    if not isinstance(semilla, int):
        raise ValueError("La semilla debe ser un número entero.")


def elegir_inicio(actividad: Actividad, generador: random.Random) -> datetime:
    duracion = timedelta(hours=actividad.duracion)
    ultimo_inicio = actividad.fecha_limite - duracion

    if ultimo_inicio <= actividad.fecha_inicio:
        return actividad.fecha_inicio

    margen = ultimo_inicio - actividad.fecha_inicio
    horas_de_margen = int(margen.total_seconds() // 3600)
    horas_de_espera = generador.randint(0, horas_de_margen)
    return actividad.fecha_inicio + timedelta(hours=horas_de_espera)


def crear_plan_aleatorio(
    recursos: Dict[str, Recurso],
    actividades: Dict[str, Actividad],
    semilla: int
) -> Planificacion:
    generador = random.Random(semilla)
    activos = [recurso for recurso in recursos.values() if recurso.activo]
    ordenadas = sorted(actividades.values(), key=lambda actividad: actividad.id)
    asignaciones = []

    for actividad in ordenadas:
        if actividad.estado != "pendiente":
            continue

        requeridas = habilidades(actividad.habilidades)
        compatibles = [
            recurso for recurso in activos
            if requeridas <= habilidades(recurso.habilidades)
        ]

        if len(compatibles) < actividad.cantidad_recursos:
            continue

        elegidos = generador.sample(compatibles, actividad.cantidad_recursos)
        ids_elegidos = tuple(recurso.id for recurso in elegidos)
        inicio = elegir_inicio(actividad, generador)
        fin = inicio + timedelta(hours=actividad.duracion)
        asignaciones.append(Asignacion(actividad.id, ids_elegidos, inicio, fin))

    return Planificacion(f"S{semilla}", tuple(asignaciones), "Plan aleatorio")


def evaluar_plan_aleatorio(datos_escenario: Dict[str, Any], semilla: int) -> Dict[str, Any]:
    recursos = datos_escenario["recursos"]
    actividades = datos_escenario["actividades"]

    plan = crear_plan_aleatorio(recursos, actividades, semilla)
    informe = MotorReglas().validar(plan, recursos, actividades)

    costo = 0.0
    for asignacion in plan.asignaciones:
        costo = costo + costo_asignacion(asignacion, recursos)

    pendientes = 0
    for actividad in actividades.values():
        if actividad.estado == "pendiente":
            pendientes = pendientes + 1

    return {
        "semilla": semilla,
        "costo": round(costo, 2),
        "violaciones_duras": len(informe.incidencias),
        "factible": informe.factible,
        "asignadas": len(plan.asignaciones),
        "sin_asignar": pendientes - len(plan.asignaciones)
    }


def evaluar_de_forma_segura(datos_escenario: Dict[str, Any], semilla: int) -> Dict[str, Any]:
    try:
        return evaluar_plan_aleatorio(datos_escenario, semilla)
    except Exception as error:
        return {"semilla": semilla, "error": f"{type(error).__name__}: {error}"}


def generar_semillas(semilla_base: int, cantidad: int) -> List[int]:
    validar_semilla(semilla_base)
    validar_cantidad(cantidad)
    return [semilla_base + i for i in range(cantidad)]


def ordenar_por_semilla(resultados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(resultados, key=lambda resultado: resultado["semilla"])


def ejecutar_secuencial(datos_escenario: Dict[str, Any], semillas: List[int]) -> Dict[str, Any]:
    resultados = []
    fallos = []

    inicio = time.perf_counter()

    for semilla in semillas:
        resultado = evaluar_de_forma_segura(datos_escenario, semilla)

        if "error" in resultado:
            fallos.append(resultado)
        else:
            resultados.append(resultado)

    segundos = time.perf_counter() - inicio

    return {
        "modalidad": "secuencial",
        "procesos": 1,
        "evaluaciones": len(semillas),
        "resultados": ordenar_por_semilla(resultados),
        "fallos": ordenar_por_semilla(fallos),
        "segundos": segundos
    }


def ejecutar_paralelo(
    datos_escenario: Dict[str, Any],
    semillas: List[int],
    procesos: int
) -> Dict[str, Any]:
    validar_procesos(procesos)

    resultados = []
    fallos = []

    inicio = time.perf_counter()

    with ProcessPoolExecutor(max_workers=procesos) as ejecutor:
        tareas = []

        for semilla in semillas:
            futuro = ejecutor.submit(evaluar_de_forma_segura, datos_escenario, semilla)
            tareas.append((semilla, futuro))

        for semilla, futuro in tareas:
            try:
                resultado = futuro.result()
            except Exception as error:
                resultado = {"semilla": semilla, "error": f"{type(error).__name__}: {error}"}

            if "error" in resultado:
                fallos.append(resultado)
            else:
                resultados.append(resultado)

    segundos = time.perf_counter() - inicio

    return {
        "modalidad": "paralelo",
        "procesos": procesos,
        "evaluaciones": len(semillas),
        "resultados": ordenar_por_semilla(resultados),
        "fallos": ordenar_por_semilla(fallos),
        "segundos": segundos
    }


def calcular_aceleracion(tiempo_secuencial: float, tiempo_paralelo: float) -> float:
    if tiempo_paralelo <= 0:
        raise ValueError("El tiempo paralelo debe ser mayor que 0.")

    if tiempo_secuencial < 0:
        raise ValueError("El tiempo secuencial no puede ser negativo.")

    return tiempo_secuencial / tiempo_paralelo


def resultados_equivalentes(
    resultados_a: List[Dict[str, Any]],
    resultados_b: List[Dict[str, Any]]
) -> bool:
    return ordenar_por_semilla(resultados_a) == ordenar_por_semilla(resultados_b)


def crear_observacion(aceleracion: float, procesos: int) -> str:
    if aceleracion >= 1:
        return (
            f"Aceleración de {aceleracion:.2f}× con {procesos} procesos. "
            "Repartir las evaluaciones entre procesos ahorró más tiempo del que "
            "costó crearlos y copiarles los datos del escenario. Aun así, esa "
            "sobrecarga existe, por eso la aceleración suele ser menor que la "
            "cantidad de procesos. El resultado depende del tamaño del escenario "
            "y de la cantidad de evaluaciones: el paralelo no siempre es mejor."
        )

    return (
        f"Desaceleración de {aceleracion:.2f}× con {procesos} procesos: el paralelo "
        "fue más lento. Crear los procesos y copiar los datos del escenario a cada "
        "uno (sobrecarga) costó más tiempo del que se ahorró repartiendo "
        "evaluaciones tan cortas. El paralelismo conviene cuando cada evaluación "
        "tarda bastante más que esa sobrecarga."
    )


def comparar_secuencial_y_paralelo(
    datos_escenario: Dict[str, Any],
    cantidad: int,
    procesos: int,
    semilla_base: int
) -> Dict[str, Any]:
    validar_procesos(procesos)
    semillas = generar_semillas(semilla_base, cantidad)

    secuencial = ejecutar_secuencial(datos_escenario, semillas)
    paralelo = ejecutar_paralelo(datos_escenario, semillas, procesos)

    aceleracion = calcular_aceleracion(secuencial["segundos"], paralelo["segundos"])
    mismos_resultados = resultados_equivalentes(secuencial["resultados"], paralelo["resultados"])
    mismos_fallos = resultados_equivalentes(secuencial["fallos"], paralelo["fallos"])

    return {
        "evaluaciones": cantidad,
        "procesos": procesos,
        "semilla_base": semilla_base,
        "secuencial": secuencial,
        "paralelo": paralelo,
        "aceleracion": aceleracion,
        "resultados_coinciden": mismos_resultados and mismos_fallos,
        "observacion": crear_observacion(aceleracion, procesos)
    }
