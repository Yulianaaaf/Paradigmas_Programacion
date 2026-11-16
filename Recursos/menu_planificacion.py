
"""Opciones de consola de RF-03 (Validar planificación) y RF-04 (Algoritmo inicial).

Este archivo es solo interfaz: pide datos y muestra resultados. Toda la
lógica está en reglas.py y algoritmo_base.py.
"""

from datetime import datetime
from typing import Dict

from .actividad import actividades
from .algoritmo_base import AlgoritmoGreedy, costo_asignacion, ejecutar
from .funciones import confirmar, leer_texto
from .modelos import Actividad, FORMATO_FECHA, Recurso
from .planificacion import Asignacion, Planificacion
from .recursos import recursos
from .reglas import MotorReglas

# Planificaciones creadas durante la sesión: {id: Planificacion}
planificaciones: Dict[str, Planificacion] = {}

motor = MotorReglas()


def formato_fecha(fecha: datetime) -> str:
    return fecha.strftime(FORMATO_FECHA)


# RF-04: EJECUTAR ALGORITMO INICIAL

def ejecutar_algoritmo_inicial() -> None:
    print("\n========== RF-04: ALGORITMO INICIAL ==========")
    print(f"Escenario: {len(recursos)} recursos y {len(actividades)} actividades registrados")
    print("Criterio de ordenamiento: prioridad; empates por fecha límite y luego ID")

    hay_recursos = any(r.activo for r in recursos.values())
    hay_actividades = any(a.estado == "pendiente" for a in actividades.values())
    if not hay_recursos or not hay_actividades:
        print("Error: debe registrar recursos activos y actividades pendientes "
              "(o cargar los datos de demostración).")
        return

    if not confirmar("¿Ejecutar el algoritmo?"):
        return

    print("Procesando...")
    id_plan = f"E{sum(1 for p in planificaciones if p.startswith('E')) + 1:03d}"
    resultado = ejecutar(AlgoritmoGreedy(), recursos, actividades, id_plan, motor)
    plan = resultado.planificacion
    planificaciones[id_plan] = plan

    retrasos = {r.actividad_id: r.horas for r in resultado.informe.retrasos}

    print(f"\n{'Actividad':<10}{'Recursos':<16}{'Inicio':<18}{'Fin':<18}"
          f"{'Costo':>12}{'Retraso (h)':>13}  Estado")
    print("-" * 97)
    for a in sorted(plan.asignaciones, key=lambda a: (a.inicio, a.actividad_id)):
        print(f"{a.actividad_id:<10}{', '.join(a.recursos_ids):<16}"
              f"{formato_fecha(a.inicio):<18}{formato_fecha(a.fin):<18}"
              f"{costo_asignacion(a, recursos):>12,.2f}{retrasos.get(a.actividad_id, 0):>13.2f}"
              f"  asignada")
    for actividad_id in sorted(plan.pendientes):
        print(f"{actividad_id:<10}{'-':<16}{'-':<18}{'-':<18}{'-':>12}{'-':>13}  pendiente")

    print("\nRESUMEN")
    print(f"Asignadas: {len(plan.asignaciones)}  |  Pendientes: {len(plan.pendientes)}")
    print(f"Costo acumulado: {resultado.costo_total:,.2f}")
    print(f"Retraso acumulado: {resultado.informe.retraso_total_horas:.2f} h")
    print(f"Tiempo de cómputo: {resultado.tiempo_segundos:.4f} s")
    print(f"Factibilidad: {resultado.informe.estado}")

    if plan.pendientes:
        print("\nMOTIVOS DE NO ASIGNACIÓN")
        for actividad_id, motivo in sorted(plan.pendientes.items()):
            print(f"- {actividad_id}: {motivo}")

    print(f"\nPlanificación {id_plan} guardada. Puede revisarla en «Validar planificación».")


# RF-03: VALIDAR PLANIFICACIÓN

def validar_planificacion() -> None:
    print("\n========== RF-03: VALIDAR PLANIFICACIÓN ==========")
    if not planificaciones:
        print("No hay planificaciones. Ejecute primero el algoritmo inicial.")
        return

    for plan in planificaciones.values():
        print(f"- {plan.id}: {plan.algoritmo} ({len(plan.asignaciones)} asignaciones)")

    id_plan = leer_texto("ID de la planificación a validar: ").upper()
    plan = planificaciones.get(id_plan)
    if plan is None:
        print("No existe una planificación con ese ID.")
        return

    informe = motor.validar(plan, recursos, actividades)
    nombres = {regla.codigo: regla.nombre for regla in motor.reglas}

    print(f"\nPlanificación {plan.id}: {informe.estado}")

    if informe.incidencias:
        print(f"\nINCIDENCIAS ({len(informe.incidencias)})")
        for codigo, incidencias in sorted(informe.agrupar("regla").items()):
            print(f"\n[{codigo}] {nombres.get(codigo, '')}")
            for i in incidencias:
                recurso = f" | Recurso: {i.recurso_id}" if i.recurso_id else ""
                print(f"  - Actividad: {', '.join(i.actividades)}{recurso}")
                print(f"    {i.descripcion}")
                if i.contexto:
                    print(f"    {i.contexto}")
    else:
        print("No se encontraron violaciones de restricciones duras.")

    print("\nRETRASOS (penalizaciones, no hacen inválida la planificación)")
    if informe.retrasos:
        for r in informe.retrasos:
            print(f"  - {r.actividad_id}: termina {formato_fecha(r.fin)}, límite "
                  f"{formato_fecha(r.fecha_limite)} -> {r.horas:.2f} h de retraso")
    else:
        print("  Ninguno")


# DATOS DE DEMOSTRACIÓN (temporal, hasta que exista RF-08)

def cargar_datos_demo() -> None:
    print("\n========== DATOS DE DEMOSTRACIÓN ==========")
    if not confirmar("Se agregarán recursos, actividades y una planificación con "
                     "errores. ¿Continuar?"):
        return

    def h(hora: int) -> datetime:
        return datetime(2026, 10, 20, hora, 0)

    nuevos_recursos = [
        Recurso("R001", "Ana (técnica)", "humano", ["electricidad"], 1, 5000, h(8), h(18)),
        Recurso("R002", "Luis (inspector)", "humano", ["inspeccion"], 1, 4000, h(8), h(18)),
        Recurso("R003", "Grúa", "equipo", ["izaje"], 1, 15000, h(8), h(12)),
        Recurso("R004", "Carlos (técnico)", "humano", ["electricidad", "soldadura"], 1, 6000, h(10), h(18)),
    ]
    nuevas_actividades = [
        Actividad("A001", "Instalar panel", 4, "alta", h(8), h(14), ["electricidad"], 1, []),
        Actividad("A002", "Instalación especializada", 6, "critica", h(8), h(16), ["electricidad"], 1, []),
        Actividad("A004", "Montaje de tablero", 3, "media", h(8), h(12), ["electricidad"], 1, []),
        Actividad("A005", "Validación de instalación", 2, "alta", h(8), h(18), ["inspeccion"], 1, ["A002"]),
        Actividad("A006", "Izaje de equipo", 5, "baja", h(8), h(18), ["izaje"], 1, []),
        Actividad("A007", "Soldadura de estructura", 2, "media", h(8), h(18), ["soldadura"], 2, []),
    ]

    agregados = 0
    for r in nuevos_recursos:
        if r.id not in recursos:
            recursos[r.id] = r
            agregados += 1
    for a in nuevas_actividades:
        if a.id not in actividades:
            actividades[a.id] = a
            agregados += 1

    # Planificación hecha "a mano" con errores, para ver al motor detectarlos.
    planificaciones["DEMO-ERR"] = Planificacion("DEMO-ERR", (
        Asignacion("A001", ["R001"], h(8), h(12)),
        Asignacion("A004", ["R001"], h(10), h(13)),   # Choca con A001 
        Asignacion("A002", ["R004"], h(10), h(16)),
        Asignacion("A005", ["R002"], h(12), h(14)),   # Empieza antes de que termine A002
        Asignacion("A006", ["R003"], h(8), h(13)),    # La grúa solo está hasta las 12
    ), "Manual (demostración con errores)")

    print(f"Se agregaron {agregados} registros nuevos (los IDs existentes no se modificaron).")
    print("Se creó la planificación DEMO-ERR para probar «Validar planificación».")
