from functools import reduce
from typing import Any, Callable, Dict, List, Sequence

from ..algoritmo_base import costo_asignacion
from ..modelos import Actividad, PRIORIDADES, Recurso
from ..planificacion import Asignacion


def filtrar_recursos_activos(recursos: Dict[str, Recurso]) -> List[Recurso]:
    return list(filter(lambda recurso: recurso.activo, recursos.values()))


def ordenar_actividades(
    actividades: Dict[str, Actividad],
    clave: Callable[[Actividad], Any]
) -> List[Actividad]:
    return sorted(actividades.values(), key=clave)


def crear_filtro_por_prioridad(prioridad: str) -> Callable[[Actividad], bool]:
    return lambda actividad: actividad.prioridad == prioridad


def agregar_actividad_al_grupo(
    grupos: Dict[str, List[str]],
    actividad: Actividad
) -> Dict[str, List[str]]:
    nuevos_grupos = dict(grupos)
    ids_anteriores = grupos.get(actividad.prioridad, [])
    nuevos_grupos[actividad.prioridad] = ids_anteriores + [actividad.id]
    return nuevos_grupos


def agrupar_actividades_por_prioridad(
    actividades: Dict[str, Actividad]
) -> Dict[str, List[str]]:
    return reduce(agregar_actividad_al_grupo, actividades.values(), {})


def contar_actividades_con_prioridad(
    actividades: Dict[str, Actividad],
    prioridad: str
) -> int:
    filtro = crear_filtro_por_prioridad(prioridad)
    return len(list(filter(filtro, actividades.values())))


def contar_actividades_por_prioridad(
    actividades: Dict[str, Actividad]
) -> Dict[str, int]:
    return {
        prioridad: contar_actividades_con_prioridad(actividades, prioridad)
        for prioridad in PRIORIDADES
    }


def obtener_costos(
    asignaciones: Sequence[Asignacion],
    recursos: Dict[str, Recurso]
) -> List[float]:
    return list(map(
        lambda asignacion: costo_asignacion(asignacion, recursos),
        asignaciones
    ))


def calcular_costo_total(
    asignaciones: Sequence[Asignacion],
    recursos: Dict[str, Recurso]
) -> float:
    costos = obtener_costos(asignaciones, recursos)
    return reduce(lambda total, costo: total + costo, costos, 0.0)


def calcular_horas_asignadas(
    recurso_id: str,
    asignaciones: Sequence[Asignacion]
) -> float:
    asignaciones_del_recurso = filter(
        lambda asignacion: recurso_id in asignacion.recursos_ids,
        asignaciones
    )
    horas = map(lambda asignacion: asignacion.duracion_horas, asignaciones_del_recurso)
    return reduce(lambda total, hora: total + hora, horas, 0.0)


def costo_por_recurso(
    asignaciones: Sequence[Asignacion],
    recursos: Dict[str, Recurso]
) -> Dict[str, float]:
    return {
        recurso.id: calcular_horas_asignadas(recurso.id, asignaciones) * recurso.costo_hora
        for recurso in recursos.values()
    }


def calcular_retraso_horas(
    asignacion: Asignacion,
    actividades: Dict[str, Actividad]
) -> float:
    actividad = actividades.get(asignacion.actividad_id)

    if actividad is None:
        return 0.0

    diferencia = asignacion.fin - actividad.fecha_limite
    return diferencia.total_seconds() / 3600


def obtener_tareas_retrasadas(
    asignaciones: Sequence[Asignacion],
    actividades: Dict[str, Actividad]
) -> Dict[str, float]:
    retrasadas = filter(
        lambda asignacion: calcular_retraso_horas(asignacion, actividades) > 0,
        asignaciones
    )
    return {
        asignacion.actividad_id: calcular_retraso_horas(asignacion, actividades)
        for asignacion in retrasadas
    }


def calcular_horas_disponibles(recurso: Recurso) -> float:
    ventana = recurso.disponibilidad_fin - recurso.disponibilidad_inicio
    return ventana.total_seconds() / 3600 * recurso.capacidad


def calcular_utilizacion(
    recurso: Recurso,
    asignaciones: Sequence[Asignacion]
) -> float:
    horas_disponibles = calcular_horas_disponibles(recurso)

    if horas_disponibles <= 0:
        return 0.0

    horas_asignadas = calcular_horas_asignadas(recurso.id, asignaciones)
    return horas_asignadas / horas_disponibles * 100


def calcular_utilizacion_por_recurso(
    recursos: Dict[str, Recurso],
    asignaciones: Sequence[Asignacion]
) -> Dict[str, float]:
    return {
        recurso.id: calcular_utilizacion(recurso, asignaciones)
        for recurso in recursos.values()
    }


def obtener_nombres_por_id(recursos: List[Recurso]) -> Dict[str, str]:
    return {recurso.id: recurso.nombre for recurso in recursos}


def obtener_prioridades_ordenadas(actividades: Dict[str, Actividad]) -> Dict[str, str]:
    ordenadas = ordenar_actividades(
        actividades,
        lambda actividad: (-PRIORIDADES.index(actividad.prioridad), actividad.id)
    )
    return {actividad.id: actividad.prioridad for actividad in ordenadas}


def aplicar_metrica(
    datos: Dict[str, Any],
    metrica: Callable[[Dict[str, Any]], Any]
) -> Any:
    return metrica(datos)


def obtener_metricas() -> Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]:
    return {
        "Recursos activos": lambda datos: obtener_nombres_por_id(
            filtrar_recursos_activos(datos["recursos"])
        ),
        "Actividades por prioridad": lambda datos: agrupar_actividades_por_prioridad(
            datos["actividades"]
        ),
        "Cantidad de actividades por prioridad": lambda datos: contar_actividades_por_prioridad(
            datos["actividades"]
        ),
        "Actividades ordenadas por prioridad": lambda datos: obtener_prioridades_ordenadas(
            datos["actividades"]
        ),
        "Costo por recurso": lambda datos: costo_por_recurso(
            datos["asignaciones"], datos["recursos"]
        ),
        "Tareas retrasadas (horas de retraso)": lambda datos: obtener_tareas_retrasadas(
            datos["asignaciones"], datos["actividades"]
        ),
        "Utilización por recurso (%)": lambda datos: calcular_utilizacion_por_recurso(
            datos["recursos"], datos["asignaciones"]
        ),
    }
