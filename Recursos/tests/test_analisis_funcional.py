import copy
from datetime import datetime
from typing import Dict, List

from ..modelos import Actividad, Recurso
from ..planificacion import Asignacion
from ..transformaciones.analisis_funcional import (
    agrupar_actividades_por_prioridad,
    aplicar_metrica,
    calcular_costo_total,
    calcular_utilizacion_por_recurso,
    contar_actividades_por_prioridad,
    costo_por_recurso,
    crear_filtro_por_prioridad,
    filtrar_recursos_activos,
    obtener_costos,
    obtener_metricas,
    obtener_tareas_retrasadas,
    ordenar_actividades
)
from ..transformaciones.analisis_imperativo import (
    agrupar_actividades_por_prioridad_imperativo,
    calcular_costo_total_imperativo,
    filtrar_recursos_activos_imperativo
)
from ..transformaciones.comparacion_enfoques import comparar_enfoques


def h(hora: int) -> datetime:
    return datetime(2026, 10, 20, hora, 0)


def crear_recurso(identificador: str, costo_hora: float = 1000, activo: bool = True) -> Recurso:
    return Recurso(
        id=identificador,
        nombre=f"Recurso {identificador}",
        tipo="humano",
        habilidades=["electricidad"],
        capacidad=1,
        costo_hora=costo_hora,
        disponibilidad_inicio=h(8),
        disponibilidad_fin=h(18),
        activo=activo
    )


def crear_actividad(identificador: str, prioridad: str = "alta", fecha_limite: int = 18) -> Actividad:
    return Actividad(
        id=identificador,
        descripcion=f"Actividad {identificador}",
        duracion=2,
        prioridad=prioridad,
        fecha_inicio=h(8),
        fecha_limite=h(fecha_limite),
        habilidades=["electricidad"],
        cantidad_recursos=1,
        dependencias=[]
    )


def crear_recursos() -> Dict[str, Recurso]:
    return {
        "R001": crear_recurso("R001", 1000),
        "R002": crear_recurso("R002", 2000, activo=False),
        "R003": crear_recurso("R003", 500),
    }


def crear_actividades() -> Dict[str, Actividad]:
    return {
        "A001": crear_actividad("A001", "alta"),
        "A002": crear_actividad("A002", "baja"),
        "A003": crear_actividad("A003", "alta", fecha_limite=10),
        "A004": crear_actividad("A004", "critica"),
    }


def crear_asignaciones_con_costos_1000_2000_3000() -> List[Asignacion]:
    return [
        Asignacion("A001", ("R001",), h(8), h(9)),
        Asignacion("A002", ("R001",), h(9), h(11)),
        Asignacion("A003", ("R001",), h(11), h(14)),
    ]


def test_costos_1000_2000_3000_suman_6000_en_ambas_versiones():
    recursos = crear_recursos()
    asignaciones = crear_asignaciones_con_costos_1000_2000_3000()

    assert obtener_costos(asignaciones, recursos) == [1000, 2000, 3000]
    assert calcular_costo_total(asignaciones, recursos) == 6000
    assert calcular_costo_total_imperativo(asignaciones, recursos) == 6000


def test_calcular_costo_no_modifica_las_asignaciones_originales():
    recursos = crear_recursos()
    asignaciones = crear_asignaciones_con_costos_1000_2000_3000()
    copia_asignaciones = copy.deepcopy(asignaciones)
    copia_recursos = copy.deepcopy(recursos)

    calcular_costo_total(asignaciones, recursos)
    costo_por_recurso(asignaciones, recursos)

    assert asignaciones == copia_asignaciones
    assert recursos == copia_recursos


def test_dos_ejecuciones_con_la_misma_entrada_dan_el_mismo_resultado():
    recursos = crear_recursos()
    actividades = crear_actividades()
    asignaciones = crear_asignaciones_con_costos_1000_2000_3000()

    assert calcular_costo_total(asignaciones, recursos) == calcular_costo_total(asignaciones, recursos)
    assert agrupar_actividades_por_prioridad(actividades) == agrupar_actividades_por_prioridad(actividades)
    assert obtener_tareas_retrasadas(asignaciones, actividades) == obtener_tareas_retrasadas(asignaciones, actividades)


def test_filtrar_recursos_activos_funcional_e_imperativo_coinciden_y_excluyen_inactivos():
    recursos = crear_recursos()

    funcional = filtrar_recursos_activos(recursos)
    imperativo = filtrar_recursos_activos_imperativo(recursos)

    assert funcional == imperativo
    assert [recurso.id for recurso in funcional] == ["R001", "R003"]


def test_agrupar_por_prioridad_funcional_e_imperativo_coinciden():
    actividades = crear_actividades()

    funcional = agrupar_actividades_por_prioridad(actividades)
    imperativo = agrupar_actividades_por_prioridad_imperativo(actividades)

    assert funcional == imperativo
    assert funcional == {"alta": ["A001", "A003"], "baja": ["A002"], "critica": ["A004"]}


def test_agrupar_no_modifica_las_actividades_originales():
    actividades = crear_actividades()
    copia = copy.deepcopy(actividades)

    agrupar_actividades_por_prioridad(actividades)
    contar_actividades_por_prioridad(actividades)

    assert actividades == copia


def test_listas_vacias_dan_resultados_vacios_o_cero():
    assert filtrar_recursos_activos({}) == []
    assert filtrar_recursos_activos_imperativo({}) == []
    assert obtener_costos([], {}) == []
    assert calcular_costo_total([], {}) == 0
    assert calcular_costo_total_imperativo([], {}) == 0
    assert agrupar_actividades_por_prioridad({}) == {}
    assert agrupar_actividades_por_prioridad_imperativo({}) == {}
    assert obtener_tareas_retrasadas([], {}) == {}
    assert costo_por_recurso([], {}) == {}
    assert calcular_utilizacion_por_recurso({}, []) == {}


def test_comparar_enfoques_marca_las_tres_operaciones_como_equivalentes():
    comparacion = comparar_enfoques(
        crear_recursos(),
        crear_actividades(),
        crear_asignaciones_con_costos_1000_2000_3000()
    )

    assert len(comparacion) == 3
    for fila in comparacion:
        assert fila["equivalentes"] is True
        assert fila["datos_sin_cambios"] is True


def test_tareas_retrasadas_calculadas_a_mano():
    actividades = crear_actividades()
    asignaciones = crear_asignaciones_con_costos_1000_2000_3000()

    assert obtener_tareas_retrasadas(asignaciones, actividades) == {"A003": 4.0}


def test_utilizacion_y_costo_por_recurso_calculados_a_mano():
    recursos = crear_recursos()
    asignaciones = crear_asignaciones_con_costos_1000_2000_3000()

    utilizacion = calcular_utilizacion_por_recurso(recursos, asignaciones)
    costos = costo_por_recurso(asignaciones, recursos)

    assert utilizacion == {"R001": 60.0, "R002": 0.0, "R003": 0.0}
    assert costos == {"R001": 6000.0, "R002": 0.0, "R003": 0.0}


def test_orden_superior_filtro_ordenamiento_y_metrica():
    actividades = crear_actividades()
    es_alta = crear_filtro_por_prioridad("alta")

    assert es_alta(actividades["A001"]) is True
    assert es_alta(actividades["A002"]) is False

    ordenadas = ordenar_actividades(actividades, lambda actividad: actividad.fecha_limite)
    assert ordenadas[0].id == "A003"

    conteo = aplicar_metrica(actividades, contar_actividades_por_prioridad)
    assert conteo == {"baja": 1, "media": 0, "alta": 2, "critica": 1}


def test_todas_las_metricas_del_menu_se_pueden_aplicar():
    datos = {
        "recursos": crear_recursos(),
        "actividades": crear_actividades(),
        "asignaciones": crear_asignaciones_con_costos_1000_2000_3000()
    }

    for metrica in obtener_metricas().values():
        assert isinstance(aplicar_metrica(datos, metrica), dict)
