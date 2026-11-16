
"""RF-04: Algoritmo base (heurística greedy, paradigma imperativo).

Arma una planificación procesando las actividades pendientes una por una,
en un orden fijo, y asignando a cada una el primer horario posible con los
recursos compatibles más baratos. Si no hay horario posible, la actividad
queda pendiente con el motivo. Nunca inventa disponibilidad.

También define:
- Planificador: la interfaz común que comparten el algoritmo base y el
  genético (RF-05), para que el resto del sistema los use igual.
- ejecutar(): corre cualquier planificador, mide el tiempo y valida el
  resultado con el motor de reglas (RF-03).

Este módulo no usa input() ni print().
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Mapping, Optional, Tuple

from .modelos import Actividad, PRIORIDADES, Recurso
from .planificacion import Asignacion, Planificacion
from .reglas import InformeValidacion, MotorReglas, habilidades

Recursos = Mapping[str, Recurso]
Actividades = Mapping[str, Actividad]


# INTERFAZ COMÚN DE LOS ALGORITMOS

class Planificador(ABC):
    """Todo algoritmo de planificación (base o genético) hereda de esta clase."""

    nombre = ""

    @abstractmethod
    def planificar(self, recursos: Recursos, actividades: Actividades,
                   id_planificacion: str) -> Planificacion:
        ...


@dataclass(frozen=True)
class ResultadoEjecucion:
    planificacion: Planificacion
    informe: InformeValidacion
    tiempo_segundos: float
    costo_total: float


def costo_asignacion(asignacion: Asignacion, recursos: Recursos) -> float:
    """Costo de una asignación: costo por hora de cada recurso x horas."""
    return sum(recursos[r].costo_hora * asignacion.duracion_horas
               for r in asignacion.recursos_ids if r in recursos)


def ejecutar(planificador: Planificador, recursos: Recursos, actividades: Actividades,
             id_planificacion: str, motor: Optional[MotorReglas] = None) -> ResultadoEjecucion:
    """Corre el algoritmo, mide su tiempo y valida el resultado con RF-03."""
    inicio = time.perf_counter()  # Reloj monotónico.
    plan = planificador.planificar(recursos, actividades, id_planificacion)
    tiempo = time.perf_counter() - inicio

    informe = (motor or MotorReglas()).validar(plan, recursos, actividades)
    costo = sum(costo_asignacion(a, recursos) for a in plan.asignaciones)
    return ResultadoEjecucion(plan, informe, tiempo, costo)


# ALGORITMO BASE

def ordenar(pendientes: List[Actividad]) -> Tuple[List[Actividad], List[Actividad]]:
    """Orden determinista: prioridad (mayor primero), fecha límite, ID.

    Una actividad solo entra al orden cuando sus dependencias pendientes ya
    entraron. Devuelve (ordenadas, bloqueadas_por_ciclo).
    """
    restantes = sorted(pendientes, key=lambda a: (
        -PRIORIDADES.index(a.prioridad), a.fecha_limite, a.id))
    ids_pendientes = {a.id for a in pendientes}
    orden: List[Actividad] = []
    listas = set()

    while restantes:
        siguiente = next((a for a in restantes
                          if all(d not in ids_pendientes or d in listas for d in a.dependencias)),
                         None)
        if siguiente is None:
            break  # Las restantes dependen entre sí en ciclo.
        orden.append(siguiente)
        listas.add(siguiente.id)
        restantes.remove(siguiente)
    return orden, restantes


class AlgoritmoGreedy(Planificador):
    nombre = "Algoritmo inicial (greedy)"

    def planificar(self, recursos, actividades, id_planificacion="P001"):
        activos = sorted((r for r in recursos.values() if r.activo),
                         key=lambda r: (r.costo_hora, r.id))
        pendientes = [a for a in actividades.values() if a.estado == "pendiente"]
        if not activos or not pendientes:
            raise ValueError("Se necesitan recursos activos y actividades pendientes")

        asignadas: Dict[str, Asignacion] = {}
        motivos: Dict[str, str] = {}
        orden, bloqueadas = ordenar(pendientes)

        for actividad in orden:
            resultado = self.asignar(actividad, activos, asignadas, actividades)
            if isinstance(resultado, Asignacion):
                asignadas[actividad.id] = resultado
            else:
                motivos[actividad.id] = resultado

        for actividad in bloqueadas:
            motivos[actividad.id] = "Sus dependencias forman un ciclo"

        return Planificacion(id_planificacion, tuple(asignadas.values()),
                             self.nombre, motivos)

    def asignar(self, actividad: Actividad, activos: List[Recurso],
                asignadas: Dict[str, Asignacion], actividades: Actividades):
        """Devuelve la Asignacion encontrada, o un texto con el motivo si no es posible."""

        # 1. Dependencias: deben estar completadas o asignadas en este plan.
        inicio_minimo = actividad.fecha_inicio
        for dep_id in actividad.dependencias:
            dependencia = actividades.get(dep_id)
            if dependencia is not None and dependencia.estado == "completada":
                continue
            if dep_id not in asignadas:
                return f"Su dependencia {dep_id} no pudo asignarse"
            inicio_minimo = max(inicio_minimo, asignadas[dep_id].fin)

        # 2. Recursos que tienen las habilidades requeridas.
        requeridas = habilidades(actividad.habilidades)
        compatibles = [r for r in activos if requeridas <= habilidades(r.habilidades)]
        if not compatibles:
            return "Ningún recurso activo tiene las habilidades: " + ", ".join(sorted(requeridas))
        if len(compatibles) < actividad.cantidad_recursos:
            return (f"Requiere {actividad.cantidad_recursos} recursos compatibles "
                    f"y solo hay {len(compatibles)}")

        # 3. Probar los momentos candidatos en orden: el inicio mínimo, cuando
        #    empieza la disponibilidad de un recurso o cuando se libera.
        duracion = timedelta(hours=actividad.duracion)
        candidatos = {inicio_minimo}
        candidatos |= {r.disponibilidad_inicio for r in compatibles}
        candidatos |= {a.fin for a in asignadas.values()}

        for inicio in sorted(c for c in candidatos if c >= inicio_minimo):
            fin = inicio + duracion
            libres = [r for r in compatibles
                      if r.disponibilidad_inicio <= inicio and fin <= r.disponibilidad_fin
                      and self.tiene_capacidad(r, inicio, fin, asignadas)]
            if len(libres) >= actividad.cantidad_recursos:
                elegidos = tuple(r.id for r in libres[:actividad.cantidad_recursos])
                return Asignacion(actividad.id, elegidos, inicio, fin)

        return "No hay horario con recursos compatibles libres dentro de su disponibilidad"

    @staticmethod
    def tiene_capacidad(recurso: Recurso, inicio: datetime, fin: datetime,
                        asignadas: Dict[str, Asignacion]) -> bool:
        """True si el recurso puede tomar una actividad más entre inicio y fin."""
        usos = [a for a in asignadas.values()
                if recurso.id in a.recursos_ids and a.inicio < fin and inicio < a.fin]
        momentos = [inicio] + [a.inicio for a in usos if a.inicio > inicio]
        maximo = max((sum(1 for a in usos if a.inicio <= m < a.fin) for m in momentos), default=0)
        return maximo < recurso.capacidad
