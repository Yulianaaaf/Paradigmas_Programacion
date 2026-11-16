import copy
import math
from typing import Any, Dict, List, Sequence

from ..modelos import Actividad, Recurso
from ..planificacion import Asignacion
from .analisis_funcional import (
    agrupar_actividades_por_prioridad,
    calcular_costo_total,
    filtrar_recursos_activos
)
from .analisis_imperativo import (
    agrupar_actividades_por_prioridad_imperativo,
    calcular_costo_total_imperativo,
    filtrar_recursos_activos_imperativo
)


def crear_fila_comparacion(
    operacion: str,
    resultado_funcional: Any,
    resultado_imperativo: Any,
    equivalentes: bool,
    datos_sin_cambios: bool
) -> Dict[str, Any]:
    return {
        "operacion": operacion,
        "resultado_funcional": resultado_funcional,
        "resultado_imperativo": resultado_imperativo,
        "equivalentes": equivalentes,
        "datos_sin_cambios": datos_sin_cambios
    }


def comparar_enfoques(
    recursos: Dict[str, Recurso],
    actividades: Dict[str, Actividad],
    asignaciones: Sequence[Asignacion]
) -> List[Dict[str, Any]]:
    copia_recursos = copy.deepcopy(recursos)
    copia_actividades = copy.deepcopy(actividades)
    copia_asignaciones = copy.deepcopy(list(asignaciones))

    activos_funcional = filtrar_recursos_activos(recursos)
    activos_imperativo = filtrar_recursos_activos_imperativo(recursos)
    recursos_sin_cambios = recursos == copia_recursos

    costo_funcional = calcular_costo_total(asignaciones, recursos)
    costo_imperativo = calcular_costo_total_imperativo(asignaciones, recursos)
    asignaciones_sin_cambios = list(asignaciones) == copia_asignaciones
    costo_sin_cambios = asignaciones_sin_cambios and recursos == copia_recursos

    grupos_funcional = agrupar_actividades_por_prioridad(actividades)
    grupos_imperativo = agrupar_actividades_por_prioridad_imperativo(actividades)
    actividades_sin_cambios = actividades == copia_actividades

    return [
        crear_fila_comparacion(
            "Filtrar recursos activos",
            activos_funcional,
            activos_imperativo,
            activos_funcional == activos_imperativo,
            recursos_sin_cambios
        ),
        crear_fila_comparacion(
            "Calcular costo total",
            costo_funcional,
            costo_imperativo,
            math.isclose(costo_funcional, costo_imperativo),
            costo_sin_cambios
        ),
        crear_fila_comparacion(
            "Agrupar actividades por prioridad",
            grupos_funcional,
            grupos_imperativo,
            grupos_funcional == grupos_imperativo,
            actividades_sin_cambios
        ),
    ]
