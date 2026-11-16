"""Pruebas del algoritmo base (RF-04). Ejecutar con: python -m pytest"""

import copy
import random
from datetime import datetime, timedelta

import pytest

from ..algoritmo_base import AlgoritmoGreedy, ejecutar, ordenar
from ..modelos import Actividad, Recurso


def h(hora: int) -> datetime:
    return datetime(2026, 10, 20, hora, 0)


def recurso(id_, **cambios) -> Recurso:
    datos = dict(id=id_, nombre=f"Recurso {id_}", tipo="humano", habilidades=["electricidad"],
                 capacidad=1, costo_hora=5000, disponibilidad_inicio=h(8), disponibilidad_fin=h(18))
    datos.update(cambios)
    return Recurso(**datos)


def actividad(id_, **cambios) -> Actividad:
    datos = dict(id=id_, descripcion=f"Actividad {id_}", duracion=4, prioridad="media",
                 fecha_inicio=h(8), fecha_limite=h(18), habilidades=["electricidad"],
                 cantidad_recursos=1, dependencias=[])
    datos.update(cambios)
    return Actividad(**datos)


def por_id(*objetos):
    return {o.id: o for o in objetos}


def planificar(recursos, actividades):
    return AlgoritmoGreedy().planificar(recursos, actividades, "P001")


# EJEMPLOS DEL ENUNCIADO

def test_ejemplo_rf04_asignacion_valida():
    # A001 (4 h) y R001 disponible 08-12: la asignación 08-12 es válida.
    recursos = por_id(recurso("R001", disponibilidad_fin=h(12)))
    plan = planificar(recursos, por_id(actividad("A001")))
    a = plan.asignacion_de("A001")
    assert (a.recursos_ids, a.inicio, a.fin) == (("R001",), h(8), h(12))


def test_ejemplo_rf04_no_inventa_disponibilidad():
    # R001 ocupado y sin alternativa: la segunda actividad queda pendiente con motivo.
    recursos = por_id(recurso("R001", disponibilidad_fin=h(12)))
    plan = planificar(recursos, por_id(actividad("A001"), actividad("A004", duracion=3)))
    assert plan.asignacion_de("A004") is None
    assert "No hay horario" in plan.pendientes["A004"]


# ORDEN

def test_prioridad_mas_alta_va_primero():
    recursos = por_id(recurso("R001", disponibilidad_fin=h(12)))
    plan = planificar(recursos, por_id(actividad("A001", prioridad="baja"),
                                       actividad("A002", prioridad="critica")))
    assert plan.asignacion_de("A002") is not None
    assert "A001" in plan.pendientes


def test_empate_se_resuelve_por_fecha_limite_y_luego_id():
    orden, _ = ordenar([actividad("A003", fecha_limite=h(16)),
                        actividad("A002", fecha_limite=h(12)),
                        actividad("A001", fecha_limite=h(16))])
    assert [a.id for a in orden] == ["A002", "A001", "A003"]


def test_dependencia_se_ordena_antes_aunque_tenga_menor_prioridad():
    orden, _ = ordenar([actividad("A005", prioridad="critica", dependencias=["A002"]),
                        actividad("A002", prioridad="baja")])
    assert [a.id for a in orden] == ["A002", "A005"]


# ASIGNACIÓN

def test_dependiente_empieza_cuando_termina_su_dependencia():
    recursos = por_id(recurso("R001"), recurso("R002", habilidades=["inspeccion"]))
    plan = planificar(recursos, por_id(
        actividad("A002", duracion=6),
        actividad("A005", duracion=2, habilidades=["inspeccion"], dependencias=["A002"])))
    assert plan.asignacion_de("A005").inicio == h(14)


def test_si_la_dependencia_falla_la_dependiente_queda_pendiente():
    recursos = por_id(recurso("R001"))
    plan = planificar(recursos, por_id(
        actividad("A002", habilidades=["soldadura"]),
        actividad("A005", dependencias=["A002"])))
    assert "A002" in plan.pendientes["A005"]


def test_respeta_el_inicio_permitido():
    plan = planificar(por_id(recurso("R001")), por_id(actividad("A001", fecha_inicio=h(10))))
    assert plan.asignacion_de("A001").inicio == h(10)


def test_espera_a_que_el_recurso_se_libere():
    plan = planificar(por_id(recurso("R001")),
                      por_id(actividad("A001", prioridad="alta"), actividad("A002")))
    assert plan.asignacion_de("A002").inicio == h(12)


def test_elige_el_recurso_mas_barato():
    recursos = por_id(recurso("R001", costo_hora=9000), recurso("R002", costo_hora=3000))
    plan = planificar(recursos, por_id(actividad("A001")))
    assert plan.asignacion_de("A001").recursos_ids == ("R002",)


def test_asigna_la_cantidad_requerida():
    recursos = por_id(recurso("R001"), recurso("R002"), recurso("R003"))
    plan = planificar(recursos, por_id(actividad("A001", cantidad_recursos=2)))
    assert len(plan.asignacion_de("A001").recursos_ids) == 2


def test_capacidad_dos_permite_actividades_simultaneas():
    plan = planificar(por_id(recurso("R001", capacidad=2)),
                      por_id(actividad("A001"), actividad("A002")))
    assert plan.asignacion_de("A001").inicio == plan.asignacion_de("A002").inicio == h(8)


def test_no_usa_recursos_inactivos():
    recursos = por_id(recurso("R001", activo=False), recurso("R002"))
    plan = planificar(recursos, por_id(actividad("A001")))
    assert plan.asignacion_de("A001").recursos_ids == ("R002",)


def test_fecha_limite_superada_genera_retraso_pero_se_asigna():
    recursos = por_id(recurso("R001"))
    resultado = ejecutar(AlgoritmoGreedy(), recursos,
                         por_id(actividad("A001", fecha_limite=h(10))), "P001")
    assert resultado.informe.factible
    assert resultado.informe.retraso_total_horas == 2


# MOTIVOS DE NO ASIGNACIÓN

def test_motivo_sin_habilidades():
    plan = planificar(por_id(recurso("R001")), por_id(actividad("A001", habilidades=["soldadura"])))
    assert "habilidades" in plan.pendientes["A001"]


def test_motivo_recursos_insuficientes():
    plan = planificar(por_id(recurso("R001")), por_id(actividad("A001", cantidad_recursos=2)))
    assert "solo hay 1" in plan.pendientes["A001"]


def test_ciclo_deja_actividades_pendientes():
    plan = planificar(por_id(recurso("R001")), por_id(
        actividad("A001", dependencias=["A002"]), actividad("A002", dependencias=["A001"])))
    assert set(plan.pendientes) == {"A001", "A002"}
    assert "ciclo" in plan.pendientes["A001"]


def test_rechaza_sin_recursos_activos():
    with pytest.raises(ValueError):
        planificar(por_id(recurso("R001", activo=False)), por_id(actividad("A001")))


# PROPIEDADES

def test_ejecutar_devuelve_costo_tiempo_y_validacion():
    resultado = ejecutar(AlgoritmoGreedy(), por_id(recurso("R001", costo_hora=1000)),
                         por_id(actividad("A001")), "P001")
    assert resultado.costo_total == 4000
    assert resultado.tiempo_segundos >= 0
    assert resultado.informe.estado == "FACTIBLE"


def test_no_modifica_los_datos_de_entrada():
    recursos, actividades = por_id(recurso("R001")), por_id(actividad("A001"), actividad("A002"))
    antes = copy.deepcopy((recursos, actividades))
    planificar(recursos, actividades)
    assert (recursos, actividades) == antes


def escenario_aleatorio(semilla: int, n_actividades=20, n_recursos=5):
    azar = random.Random(semilla)
    hab = ["electricidad", "soldadura", "inspeccion", "redes"]
    recursos = por_id(*[recurso(
        f"R{i:03d}", habilidades=azar.sample(hab, 2), capacidad=azar.randint(1, 2),
        costo_hora=azar.randint(1, 10) * 1000,
        disponibilidad_inicio=h(azar.randint(6, 10)),
        disponibilidad_fin=h(10) + timedelta(days=azar.randint(1, 3))) for i in range(n_recursos)])
    actividades = por_id(*[actividad(
        f"A{i:03d}", duracion=azar.randint(1, 6),
        prioridad=azar.choice(["baja", "media", "alta", "critica"]),
        habilidades=[azar.choice(hab)], cantidad_recursos=azar.randint(1, 2),
        fecha_limite=h(12) + timedelta(days=azar.randint(0, 2)),
        dependencias=azar.sample([f"A{j:03d}" for j in range(i)], min(i, azar.randint(0, 2))))
        for i in range(n_actividades)])
    return recursos, actividades


@pytest.mark.parametrize("semilla", [2026, 2027, 7])
def test_resultado_siempre_factible_en_escenarios_aleatorios(semilla):
    recursos, actividades = escenario_aleatorio(semilla)
    resultado = ejecutar(AlgoritmoGreedy(), recursos, actividades, "P001")
    assert resultado.informe.factible, resultado.informe.incidencias
    total = len(resultado.planificacion.asignaciones) + len(resultado.planificacion.pendientes)
    assert total == len(actividades)


def test_es_reproducible():
    recursos, actividades = escenario_aleatorio(2026)
    assert planificar(recursos, actividades) == planificar(recursos, actividades)
