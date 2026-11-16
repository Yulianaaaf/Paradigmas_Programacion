import copy
import os
from datetime import datetime
from typing import Any, Dict

import pytest

from ..modelos import Actividad, Recurso
from ..paralelismo.comparador_paralelo import (
    calcular_aceleracion,
    comparar_secuencial_y_paralelo,
    ejecutar_paralelo,
    ejecutar_secuencial,
    evaluar_de_forma_segura,
    evaluar_plan_aleatorio,
    generar_semillas,
    resultados_equivalentes
)


def h(hora: int) -> datetime:
    return datetime(2026, 10, 20, hora, 0)


def crear_escenario() -> Dict[str, Any]:
    recursos = {
        "R001": Recurso("R001", "Ana", "humano", ["electricidad"], 1, 5000, h(8), h(18)),
        "R002": Recurso("R002", "Luis", "humano", ["electricidad", "inspeccion"], 1, 4000, h(8), h(18)),
        "R003": Recurso("R003", "Grúa", "equipo", ["izaje"], 1, 15000, h(8), h(12)),
    }
    actividades = {
        "A001": Actividad("A001", "Instalar panel", 4, "alta", h(8), h(16), ["electricidad"], 1, []),
        "A002": Actividad("A002", "Inspección", 2, "media", h(8), h(18), ["inspeccion"], 1, ["A001"]),
        "A003": Actividad("A003", "Izaje", 3, "baja", h(8), h(12), ["izaje"], 1, []),
        "A004": Actividad("A004", "Cableado", 2, "critica", h(8), h(14), ["electricidad"], 2, []),
    }
    return {"recursos": recursos, "actividades": actividades}


def test_calcular_aceleracion_y_desaceleracion():
    assert calcular_aceleracion(8, 5) == 1.6
    assert calcular_aceleracion(8, 10) == 0.8


def test_calcular_aceleracion_con_tiempo_paralelo_cero_lanza_error():
    with pytest.raises(ValueError):
        calcular_aceleracion(8, 0)


def test_generar_semillas_consecutivas():
    assert generar_semillas(2026, 4) == [2026, 2027, 2028, 2029]


def test_misma_semilla_da_el_mismo_resultado():
    escenario = crear_escenario()

    primera = evaluar_plan_aleatorio(escenario, 2026)
    segunda = evaluar_plan_aleatorio(escenario, 2026)

    assert primera == segunda
    assert set(primera) == {"semilla", "costo", "violaciones_duras", "factible", "asignadas", "sin_asignar"}


def test_evaluar_no_modifica_los_datos_del_escenario():
    escenario = crear_escenario()
    copia = copy.deepcopy(escenario)

    evaluar_plan_aleatorio(escenario, 7)

    assert escenario == copia


def test_secuencial_y_paralelo_dan_resultados_equivalentes():
    escenario = crear_escenario()
    semillas = generar_semillas(2026, 4)

    secuencial = ejecutar_secuencial(escenario, semillas)
    paralelo = ejecutar_paralelo(escenario, semillas, 2)

    assert len(secuencial["resultados"]) == 4
    assert resultados_equivalentes(secuencial["resultados"], paralelo["resultados"])
    assert secuencial["fallos"] == []
    assert paralelo["fallos"] == []


def test_comparar_devuelve_tiempos_aceleracion_y_equivalencia():
    comparacion = comparar_secuencial_y_paralelo(crear_escenario(), 4, 2, 2026)

    assert comparacion["evaluaciones"] == 4
    assert comparacion["secuencial"]["segundos"] > 0
    assert comparacion["paralelo"]["segundos"] > 0
    assert comparacion["aceleracion"] > 0
    assert comparacion["resultados_coinciden"] is True
    assert "aceleración" in comparacion["observacion"].lower()


@pytest.mark.parametrize("cantidad, procesos", [
    (0, 2),
    (4, 0),
    (4, (os.cpu_count() or 1) + 1),
])
def test_parametros_invalidos_lanzan_value_error(cantidad, procesos):
    with pytest.raises(ValueError):
        comparar_secuencial_y_paralelo(crear_escenario(), cantidad, procesos, 2026)


def test_semilla_no_entera_lanza_value_error():
    with pytest.raises(ValueError):
        generar_semillas("abc", 4)


def test_evaluacion_que_falla_queda_registrada_sin_detener_la_ejecucion():
    datos_invalidos = {"recursos": {}}

    resultado = evaluar_de_forma_segura(datos_invalidos, 5)
    assert resultado["semilla"] == 5
    assert "error" in resultado

    secuencial = ejecutar_secuencial(datos_invalidos, [1, 2, 3])
    paralelo = ejecutar_paralelo(datos_invalidos, [1, 2, 3], 2)

    assert len(secuencial["fallos"]) == 3
    assert len(paralelo["fallos"]) == 3
    assert secuencial["resultados"] == []
    assert resultados_equivalentes(secuencial["fallos"], paralelo["fallos"])
