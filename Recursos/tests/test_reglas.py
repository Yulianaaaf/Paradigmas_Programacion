"""Pruebas del motor de reglas (RF-03).

Ejecutar desde la carpeta Recursos con:  python -m pytest
"""

import copy
from datetime import datetime

import pytest

from ..modelos import Actividad, Recurso
from ..planificacion import Asignacion, Planificacion
from ..reglas import Incidencia, MotorReglas, Regla, tramos_excedidos


# DATOS DE PRUEBA

def h(hora: int) -> datetime:
    """Atajo: h(8) = 2026-10-20 08:00."""
    return datetime(2026, 10, 20, hora, 0)


def recurso(id_: str, **cambios) -> Recurso:
    datos = dict(
        id=id_, nombre=f"Recurso {id_}", tipo="humano",
        habilidades=["electricidad"], capacidad=1, costo_hora=5000,
        disponibilidad_inicio=h(8), disponibilidad_fin=h(18),
    )
    datos.update(cambios)
    return Recurso(**datos)


def actividad(id_: str, **cambios) -> Actividad:
    datos = dict(
        id=id_, descripcion=f"Actividad {id_}", duracion=4, prioridad="alta",
        fecha_inicio=h(8), fecha_limite=h(18), habilidades=["electricidad"],
        cantidad_recursos=1, dependencias=[],
    )
    datos.update(cambios)
    return Actividad(**datos)


def plan(*asignaciones: Asignacion) -> Planificacion:
    return Planificacion(id="P001", asignaciones=asignaciones)


def codigos(informe) -> list:
    return sorted(incidencia.codigo for incidencia in informe.incidencias)


@pytest.fixture
def recursos():
    return {"R001": recurso("R001"), "R002": recurso("R002")}


@pytest.fixture
def actividades():
    return {
        "A001": actividad("A001"),
        "A002": actividad("A002"),
        "A004": actividad("A004", duracion=3),
        "A005": actividad("A005", duracion=2, dependencias=["A002"]),
    }


@pytest.fixture
def motor():
    return MotorReglas()


# CASO VÁLIDO

def test_planificacion_valida_es_factible(motor, recursos, actividades):
    p = plan(
        Asignacion("A001", ["R001"], h(8), h(12)),
        Asignacion("A002", ["R002"], h(8), h(12)),
        Asignacion("A005", ["R002"], h(12), h(14)),
    )
    informe = motor.validar(p, recursos, actividades)
    assert informe.factible
    assert informe.estado == "FACTIBLE"


def test_motor_tiene_las_nueve_reglas(motor):
    assert [r.codigo for r in motor.reglas] == [f"R0{i}" for i in range(1, 10)]


# CADA REGLA

def test_r01_actividad_inexistente(motor, recursos, actividades):
    informe = motor.validar(plan(Asignacion("A999", ["R001"], h(8), h(12))), recursos, actividades)
    assert codigos(informe) == ["R01"]


def test_r01_recurso_inexistente(motor, recursos, actividades):
    informe = motor.validar(plan(Asignacion("A001", ["R999"], h(8), h(12))), recursos, actividades)
    assert codigos(informe) == ["R01"]
    assert informe.incidencias[0].recurso_id == "R999"


def test_r02_recurso_inactivo(motor, recursos, actividades):
    recursos["R001"].activo = False
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(12))), recursos, actividades)
    assert codigos(informe) == ["R02"]


def test_r03_habilidad_faltante(motor, recursos, actividades):
    recursos["R001"].habilidades = ["soldadura"]
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(12))), recursos, actividades)
    assert codigos(informe) == ["R03"]
    assert "electricidad" in informe.incidencias[0].descripcion


def test_r03_habilidades_sin_importar_mayusculas(motor, recursos, actividades):
    recursos["R001"].habilidades = ["Electricidad "]
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(12))), recursos, actividades)
    assert informe.factible


def test_r04_ejemplo_rf01_fuera_de_disponibilidad(motor, recursos, actividades):
    # R002 disponible 08-12: una tarea 11-14 no puede usarlo.
    recursos["R002"].disponibilidad_fin = h(12)
    actividades["A004"].fecha_inicio = h(8)
    informe = motor.validar(plan(Asignacion("A004", ["R002"], h(11), h(14))), recursos, actividades)
    assert codigos(informe) == ["R04"]


def test_r04_justo_en_el_borde_es_valido(motor, recursos, actividades):
    recursos["R001"].disponibilidad_fin = h(12)
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(12))), recursos, actividades)
    assert informe.factible


def test_r05_ejemplo_rf03_conflicto_de_capacidad(motor, recursos, actividades):
    # R001 (capacidad 1) en A001 08-12 y A004 10-13 -> conflicto 10:00-12:00.
    informe = motor.validar(plan(
        Asignacion("A001", ["R001"], h(8), h(12)),
        Asignacion("A004", ["R001"], h(10), h(13)),
    ), recursos, actividades)
    assert codigos(informe) == ["R05"]
    incidencia = informe.incidencias[0]
    assert incidencia.actividades == ("A001", "A004")
    assert incidencia.recurso_id == "R001"
    assert "10:00" in incidencia.contexto and "12:00" in incidencia.contexto


def test_r05_capacidad_dos_permite_dos_simultaneas(motor, recursos, actividades):
    recursos["R001"].capacidad = 2
    informe = motor.validar(plan(
        Asignacion("A001", ["R001"], h(8), h(12)),
        Asignacion("A004", ["R001"], h(10), h(13)),
    ), recursos, actividades)
    assert informe.factible


def test_r05_tareas_contiguas_no_chocan():
    # Una termina a las 12 y otra empieza a las 12: no hay superposición.
    assert tramos_excedidos([("A", h(8), h(12)), ("B", h(12), h(14))], 1) == []


def test_r06_cantidad_insuficiente(motor, recursos, actividades):
    actividades["A001"].cantidad_recursos = 2
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(12))), recursos, actividades)
    assert codigos(informe) == ["R06"]


def test_r07_ejemplo_rf03_dependencia_incumplida(motor, recursos, actividades):
    # A005 comienza antes de terminar A002.
    informe = motor.validar(plan(
        Asignacion("A002", ["R001"], h(8), h(12)),
        Asignacion("A005", ["R002"], h(10), h(12)),
    ), recursos, actividades)
    assert codigos(informe) == ["R07"]
    assert "A002" in informe.incidencias[0].descripcion


def test_r07_dependencia_sin_asignar(motor, recursos, actividades):
    informe = motor.validar(plan(Asignacion("A005", ["R002"], h(12), h(14))), recursos, actividades)
    assert codigos(informe) == ["R07"]


def test_r07_dependencia_ya_completada_es_valida(motor, recursos, actividades):
    actividades["A002"].estado = "completada"
    informe = motor.validar(plan(Asignacion("A005", ["R002"], h(8), h(10))), recursos, actividades)
    assert informe.factible


def test_r08_inicio_antes_de_lo_permitido(motor, recursos, actividades):
    actividades["A001"].fecha_inicio = h(9)
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(12))), recursos, actividades)
    assert codigos(informe) == ["R08"]


def test_r09_actividad_asignada_dos_veces(motor, recursos, actividades):
    informe = motor.validar(plan(
        Asignacion("A001", ["R001"], h(8), h(12)),
        Asignacion("A001", ["R002"], h(8), h(12)),
    ), recursos, actividades)
    assert codigos(informe) == ["R09"]


def test_r09_duracion_no_coincide(motor, recursos, actividades):
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(10))), recursos, actividades)
    assert codigos(informe) == ["R09"]


# RETRASOS: penalización separada

def test_retraso_no_hace_infactible(motor, recursos, actividades):
    actividades["A001"].fecha_limite = h(10)
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(12))), recursos, actividades)
    assert informe.factible
    assert len(informe.retrasos) == 1
    assert informe.retraso_total_horas == 2


# PROPIEDADES DEL MOTOR

def test_validar_no_modifica_los_datos(motor, recursos, actividades):
    p = plan(
        Asignacion("A001", ["R001"], h(8), h(12)),
        Asignacion("A004", ["R001"], h(10), h(13)),
    )
    antes = (copy.deepcopy(p), copy.deepcopy(recursos), copy.deepcopy(actividades))
    motor.validar(p, recursos, actividades)
    assert (p, recursos, actividades) == antes


def test_reporte_agrupado_por_regla_actividad_y_recurso(motor, recursos, actividades):
    recursos["R001"].activo = False
    informe = motor.validar(plan(
        Asignacion("A001", ["R001"], h(8), h(12)),
        Asignacion("A004", ["R001"], h(10), h(13)),
    ), recursos, actividades)
    assert set(informe.por_regla()) == {"R02", "R05"}
    assert set(informe.por_actividad()) == {"A001", "A004"}
    assert set(informe.por_recurso()) == {"R001"}


def test_agregar_regla_nueva_sin_modificar_el_motor(motor, recursos, actividades):
    class MaximoOchoHoras(Regla):
        codigo = "R10"
        nombre = "Máximo 8 horas"

        def evaluar(self, contexto):
            return [
                Incidencia(self.codigo, "Supera 8 horas", (a.actividad_id,))
                for a in contexto.planificacion.asignaciones
                if a.duracion_horas > 8
            ]

    motor.agregar_regla(MaximoOchoHoras())
    actividades["A001"].duracion = 9
    informe = motor.validar(plan(Asignacion("A001", ["R001"], h(8), h(17))), recursos, actividades)
    assert codigos(informe) == ["R10"]


def test_no_permite_codigos_de_regla_repetidos(motor):
    with pytest.raises(ValueError):
        motor.agregar_regla(motor.reglas[0])


def test_asignacion_con_horario_invertido_es_invalida():
    with pytest.raises(ValueError):
        Asignacion("A001", ["R001"], h(12), h(8))
