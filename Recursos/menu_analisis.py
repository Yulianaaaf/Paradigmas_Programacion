from typing import Any, Dict, List, Optional

from .actividad import actividades
from .algoritmo_base import AlgoritmoGreedy
from .funciones import pausar
from .menu_planificacion import ejecutar_algoritmo_inicial, planificaciones
from .modelos import Recurso
from .paralelismo.comparador_paralelo import (
    comparar_secuencial_y_paralelo,
    ejecutar_paralelo,
    ejecutar_secuencial,
    generar_semillas,
    obtener_maximo_procesos
)
from .planificacion import Planificacion
from .recursos import recursos
from .transformaciones.analisis_funcional import aplicar_metrica, obtener_metricas
from .transformaciones.comparacion_enfoques import comparar_enfoques


def formatear_valor(valor: Any) -> str:
    if isinstance(valor, bool):
        return "Sí" if valor else "No"

    if isinstance(valor, float):
        return f"{valor:,.2f}"

    if isinstance(valor, Recurso):
        return valor.id

    if isinstance(valor, list):
        textos = [formatear_valor(elemento) for elemento in valor]
        return ", ".join(textos) if textos else "(ninguno)"

    if isinstance(valor, dict):
        textos = [f"{clave}: {formatear_valor(dato)}" for clave, dato in valor.items()]
        return "; ".join(textos) if textos else "(ninguno)"

    return str(valor)


def leer_entero_con_valor_por_defecto(mensaje: str, valor_por_defecto: int) -> int:
    while True:
        texto = input(f"{mensaje} (Enter = {valor_por_defecto}): ").strip()

        if not texto:
            return valor_por_defecto

        try:
            return int(texto)

        except ValueError:
            print("Error: ingresá un número entero válido.")


def obtener_ultima_planificacion_base() -> str:
    ids_algoritmo_base = [
        id_plan for id_plan, plan in planificaciones.items()
        if plan.algoritmo == AlgoritmoGreedy.nombre
    ]

    if ids_algoritmo_base:
        return ids_algoritmo_base[-1]

    return list(planificaciones)[-1]


def seleccionar_planificacion() -> Optional[Planificacion]:
    if not planificaciones:
        print("No hay planificaciones en memoria. Se ofrece ejecutar el algoritmo inicial.")
        ejecutar_algoritmo_inicial()

    if not planificaciones:
        print("Primero ejecute el algoritmo inicial.")
        return None

    print("\nPlanificaciones disponibles:")
    for plan in planificaciones.values():
        print(f"- {plan.id}: {plan.algoritmo} ({len(plan.asignaciones)} asignaciones)")

    id_por_defecto = obtener_ultima_planificacion_base()
    id_plan = input(
        f"ID de la planificación a analizar (Enter = {id_por_defecto}): "
    ).strip().upper()

    if not id_plan:
        id_plan = id_por_defecto

    plan = planificaciones.get(id_plan)

    if plan is None:
        print("No existe una planificación con ese ID.")

    return plan


def mostrar_metrica(nombre: str, resultado: Dict[str, Any]) -> None:
    print(f"\n{nombre.upper()}")

    if not resultado:
        print("Sin resultados.")
        return

    print(f"{'Elemento':<14}Valor")
    print("-" * 60)

    for clave, valor in resultado.items():
        print(f"{clave:<14}{formatear_valor(valor)}")


def mostrar_comparacion_enfoques(comparacion: List[Dict[str, Any]]) -> None:
    print("\nCOMPARACIÓN FUNCIONAL VS. IMPERATIVO")

    for fila in comparacion:
        print("\n" + "-" * 60)
        print(f"Operación: {fila['operacion']}")
        print(f"  Funcional:   {formatear_valor(fila['resultado_funcional'])}")
        print(f"  Imperativo:  {formatear_valor(fila['resultado_imperativo'])}")
        print(f"  ¿Equivalentes?: {formatear_valor(fila['equivalentes'])}")
        print(f"  ¿Datos originales sin cambios?: {formatear_valor(fila['datos_sin_cambios'])}")


def menu_analisis_funcional() -> None:
    print("\n========== RF-06: ANÁLISIS FUNCIONAL ==========")

    if not recursos or not actividades:
        print("No hay datos cargados. Registre recursos y actividades "
              "o cargue los datos de demostración.")
        pausar()
        return

    plan = seleccionar_planificacion()

    if plan is None:
        pausar()
        return

    datos = {
        "recursos": recursos,
        "actividades": actividades,
        "asignaciones": plan.asignaciones
    }
    metricas = obtener_metricas()
    nombres = list(metricas)
    opcion_comparacion = str(len(nombres) + 1)

    while True:
        print(f"\n========== RF-06: ANÁLISIS FUNCIONAL ({plan.id}) ==========")

        for numero, nombre in enumerate(nombres, start=1):
            print(f"{numero}. {nombre}")

        print(f"{opcion_comparacion}. Comparar enfoque funcional e imperativo")
        print("0. Volver al menú principal")

        opcion = input("Elegí una opción: ").strip()

        if opcion == "0":
            break

        if opcion == opcion_comparacion:
            comparacion = comparar_enfoques(recursos, actividades, plan.asignaciones)
            mostrar_comparacion_enfoques(comparacion)

        elif opcion.isdigit() and 1 <= int(opcion) <= len(nombres):
            nombre = nombres[int(opcion) - 1]
            resultado = aplicar_metrica(datos, metricas[nombre])
            mostrar_metrica(nombre, resultado)

        else:
            print("Opción inválida.")

        pausar()


def mostrar_ejecucion(ejecucion: Dict[str, Any]) -> None:
    resultados = ejecucion["resultados"]
    fallos = ejecucion["fallos"]
    factibles = [resultado for resultado in resultados if resultado["factible"]]

    print(f"\nMODALIDAD: {ejecucion['modalidad'].upper()} ({ejecucion['procesos']} proceso(s))")
    print(f"Evaluaciones: {ejecucion['evaluaciones']}  |  Exitosas: {len(resultados)}"
          f"  |  Fallos: {len(fallos)}  |  Factibles: {len(factibles)}")
    print(f"Tiempo total: {ejecucion['segundos']:.4f} s")

    if resultados:
        print(f"\n{'Semilla':<10}{'Costo':>14}{'Violaciones':>14}{'Sin asignar':>13}  Factible")
        print("-" * 62)

        for resultado in resultados[:10]:
            print(f"{resultado['semilla']:<10}{resultado['costo']:>14,.2f}"
                  f"{resultado['violaciones_duras']:>14}{resultado['sin_asignar']:>13}"
                  f"  {formatear_valor(resultado['factible'])}")

        if len(resultados) > 10:
            print(f"(Se muestran 10 de {len(resultados)} resultados)")

    for fallo in fallos[:5]:
        print(f"Fallo en semilla {fallo['semilla']}: {fallo['error']}")


def mostrar_comparacion_paralela(comparacion: Dict[str, Any]) -> None:
    secuencial = comparacion["secuencial"]
    paralelo = comparacion["paralelo"]

    print("\nCOMPARACIÓN SECUENCIAL VS. PARALELO")
    print(f"Evaluaciones: {comparacion['evaluaciones']}  |  Procesos: {comparacion['procesos']}"
          f"  |  Semilla base: {comparacion['semilla_base']}")
    print(f"\n{'Modalidad':<14}{'Tiempo (s)':>12}{'Exitosas':>10}{'Fallos':>8}")
    print("-" * 44)
    print(f"{'Secuencial':<14}{secuencial['segundos']:>12.4f}"
          f"{len(secuencial['resultados']):>10}{len(secuencial['fallos']):>8}")
    print(f"{'Paralelo':<14}{paralelo['segundos']:>12.4f}"
          f"{len(paralelo['resultados']):>10}{len(paralelo['fallos']):>8}")
    print(f"\nAceleración (secuencial / paralelo): {comparacion['aceleracion']:.2f}×")
    print(f"¿Los resultados coinciden?: {formatear_valor(comparacion['resultados_coinciden'])}")
    print(f"Observación: {comparacion['observacion']}")


def menu_comparar_paralelo() -> None:
    hay_recursos = any(recurso.activo for recurso in recursos.values())
    hay_actividades = any(actividad.estado == "pendiente" for actividad in actividades.values())

    if not hay_recursos or not hay_actividades:
        print("\nDebe cargar o generar un escenario: registre recursos activos y "
              "actividades pendientes o cargue los datos de demostración.")
        pausar()
        return

    datos_escenario = {"recursos": recursos, "actividades": actividades}

    while True:
        print("\n========== RF-07: COMPARAR SECUENCIAL Y PARALELO ==========")
        print(f"Escenario: {len(recursos)} recursos y {len(actividades)} actividades registrados")
        print("1. Ejecutar secuencial")
        print("2. Ejecutar paralelo")
        print("3. Comparar")
        print("0. Volver al menú principal")

        opcion = input("Elegí una opción: ").strip()

        if opcion == "0":
            break

        if opcion not in ("1", "2", "3"):
            print("Opción inválida.")
            pausar()
            continue

        cantidad = leer_entero_con_valor_por_defecto("Cantidad de evaluaciones", 50)
        procesos = 1

        if opcion != "1":
            procesos = leer_entero_con_valor_por_defecto(
                "Cantidad de procesos", obtener_maximo_procesos()
            )

        semilla = leer_entero_con_valor_por_defecto("Semilla", 2026)

        try:
            if opcion == "1":
                semillas = generar_semillas(semilla, cantidad)
                print("Procesando...")
                mostrar_ejecucion(ejecutar_secuencial(datos_escenario, semillas))

            elif opcion == "2":
                semillas = generar_semillas(semilla, cantidad)
                print("Procesando...")
                mostrar_ejecucion(ejecutar_paralelo(datos_escenario, semillas, procesos))

            else:
                print("Procesando...")
                comparacion = comparar_secuencial_y_paralelo(
                    datos_escenario, cantidad, procesos, semilla
                )
                mostrar_comparacion_paralela(comparacion)

        except ValueError as error:
            print(f"Error: {error}")

        pausar()
