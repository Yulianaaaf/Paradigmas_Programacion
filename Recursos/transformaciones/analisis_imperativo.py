from typing import Dict, List, Sequence

from ..modelos import Actividad, Recurso
from ..planificacion import Asignacion


def filtrar_recursos_activos_imperativo(recursos: Dict[str, Recurso]) -> List[Recurso]:
    activos = []

    for recurso in recursos.values():
        if recurso.activo:
            activos.append(recurso)

    return activos


def calcular_costo_total_imperativo(
    asignaciones: Sequence[Asignacion],
    recursos: Dict[str, Recurso]
) -> float:
    total = 0.0

    for asignacion in asignaciones:
        costo_de_la_asignacion = 0

        for recurso_id in asignacion.recursos_ids:
            if recurso_id in recursos:
                costo_hora = recursos[recurso_id].costo_hora
                costo_de_la_asignacion = costo_de_la_asignacion + costo_hora * asignacion.duracion_horas

        total = total + costo_de_la_asignacion

    return total


def agrupar_actividades_por_prioridad_imperativo(
    actividades: Dict[str, Actividad]
) -> Dict[str, List[str]]:
    grupos = {}

    for actividad in actividades.values():
        if actividad.prioridad not in grupos:
            grupos[actividad.prioridad] = []

        grupos[actividad.prioridad].append(actividad.id)

    return grupos
