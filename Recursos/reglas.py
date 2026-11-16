
"""RF-03: Motor de reglas y restricciones.

Revisa una planificación sin modificarla y devuelve un informe con:
- estado FACTIBLE / NO FACTIBLE,
- incidencias (violaciones de restricciones duras),
- retrasos, por separado (son penalizaciones, no violaciones).

Cada regla es una clase independiente. Para agregar una regla nueva se crea
otra clase y se registra con agregar_regla(), sin modificar el motor.
Este módulo no usa input() ni print(): el menú es quien muestra el informe.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Mapping, Optional, Tuple

from .modelos import Actividad, Recurso, FORMATO_FECHA
from .planificacion import Asignacion, Planificacion

Recursos = Mapping[str, Recurso]
Actividades = Mapping[str, Actividad]

@dataclass(frozen=True)
class Incidencia:
    codigo: str
    descripcion: str
    actividades: Tuple[str, ...]
    recurso_id: Optional[str] = None
    contexto: str = ""


@dataclass(frozen=True)
class Retraso:
    actividad_id: str
    fin: datetime
    fecha_limite: datetime
    horas: float


@dataclass(frozen=True)
class InformeValidacion:
    planificacion_id: str
    incidencias: Tuple[Incidencia, ...]
    retrasos: Tuple[Retraso, ...]

    @property
    def factible(self) -> bool:
        return not self.incidencias

    @property
    def estado(self) -> str:
        return "FACTIBLE" if self.factible else "NO FACTIBLE"

    @property
    def retraso_total_horas(self) -> float:
        return sum(r.horas for r in self.retrasos)

    def agrupar(self, criterio: str) -> Dict[str, List[Incidencia]]:
        """Agrupa las incidencias por 'regla', 'actividad' o 'recurso'."""
        claves = {
            "regla": lambda i: [i.codigo],
            "actividad": lambda i: list(i.actividades),
            "recurso": lambda i: [i.recurso_id] if i.recurso_id else [],
        }[criterio]
        grupos: Dict[str, List[Incidencia]] = {}
        for incidencia in self.incidencias:
            for clave in claves(incidencia):
                grupos.setdefault(clave, []).append(incidencia)
        return grupos


# AUXILIARES

def fecha(valor: datetime) -> str:
    return valor.strftime(FORMATO_FECHA)


def habilidades(lista: List[str]) -> set:
    """Normaliza habilidades para compararlas sin importar mayúsculas."""
    return {h.strip().lower() for h in lista}


def recursos_de(asignacion: Asignacion, recursos: Recursos) -> List[Recurso]:
    """Recursos existentes de una asignación (los inexistentes los reporta R01)."""
    return [recursos[r] for r in dict.fromkeys(asignacion.recursos_ids) if r in recursos]


# CLASES BASE

class Regla(ABC):
    codigo = ""
    nombre = ""

    @abstractmethod
    def evaluar(self, plan: Planificacion, recursos: Recursos,
                actividades: Actividades) -> List[Incidencia]:
        """Devuelve las incidencias encontradas (vacía si todo está bien)."""


class ReglaPorAsignacion(Regla):
    """Base para reglas que revisan cada asignación por separado."""

    def evaluar(self, plan, recursos, actividades):
        incidencias = []
        for asignacion in plan.asignaciones:
            actividad = actividades.get(asignacion.actividad_id)
            if actividad is not None:  
                incidencias += self.revisar(asignacion, actividad, plan, recursos, actividades)
        return incidencias

    @abstractmethod
    def revisar(self, asignacion: Asignacion, actividad: Actividad, plan: Planificacion,
                recursos: Recursos, actividades: Actividades) -> List[Incidencia]:
        ...

    def crear(self, descripcion: str, asignacion: Asignacion,
              recurso_id: Optional[str] = None) -> Incidencia:
        return Incidencia(self.codigo, descripcion, (asignacion.actividad_id,),
                          recurso_id, f"Horario: {asignacion.horario()}")


# LAS 9 RESTRICCIONES DURAS

class IntegridadReferencias(Regla):
    codigo, nombre = "R01", "Integridad de referencias"

    def evaluar(self, plan, recursos, actividades):
        incidencias = []
        for a in plan.asignaciones:
            if a.actividad_id not in actividades:
                incidencias.append(Incidencia(
                    self.codigo, f"La actividad {a.actividad_id} no existe", (a.actividad_id,)))
            for r in a.recursos_ids:
                if r not in recursos:
                    incidencias.append(Incidencia(
                        self.codigo, f"El recurso {r} no existe", (a.actividad_id,), r))
        return incidencias


class RecursoActivo(ReglaPorAsignacion):
    codigo, nombre = "R02", "Estado activo"

    def revisar(self, asignacion, actividad, plan, recursos, actividades):
        return [self.crear(f"El recurso {r.id} está inactivo", asignacion, r.id)
                for r in recursos_de(asignacion, recursos) if not r.activo]


class HabilidadesCompatibles(ReglaPorAsignacion):
    codigo, nombre = "R03", "Habilidades compatibles"

    def revisar(self, asignacion, actividad, plan, recursos, actividades):
        incidencias = []
        for r in recursos_de(asignacion, recursos):
            faltantes = habilidades(actividad.habilidades) - habilidades(r.habilidades)
            if faltantes:
                incidencias.append(self.crear(
                    f"El recurso {r.id} no tiene: {', '.join(sorted(faltantes))}",
                    asignacion, r.id))
        return incidencias


class DisponibilidadCompleta(ReglaPorAsignacion):
    codigo, nombre = "R04", "Disponibilidad completa"

    def revisar(self, asignacion, actividad, plan, recursos, actividades):
        return [
            self.crear(f"El recurso {r.id} solo está disponible de "
                       f"{fecha(r.disponibilidad_inicio)} a {fecha(r.disponibilidad_fin)}",
                       asignacion, r.id)
            for r in recursos_de(asignacion, recursos)
            if not (r.disponibilidad_inicio <= asignacion.inicio
                    and asignacion.fin <= r.disponibilidad_fin)
        ]


class CapacidadSimultanea(Regla):
    """Para cada recurso, revisa el inicio de cada una de sus asignaciones:
    si en ese instante hay más actividades en curso que su capacidad, hay
    conflicto. El intervalo superpuesto va del inicio más tardío al fin más
    temprano de las actividades involucradas."""
    codigo, nombre = "R05", "Capacidad simultánea"

    def evaluar(self, plan, recursos, actividades):
        incidencias, reportados = [], set()
        for recurso in recursos.values():
            usos = [a for a in plan.asignaciones if recurso.id in a.recursos_ids]
            for actual in usos:
                en_curso = [a for a in usos if a.inicio <= actual.inicio < a.fin]
                ids = tuple(sorted(a.actividad_id for a in en_curso))
                if len(en_curso) > recurso.capacidad and ids not in reportados:
                    reportados.add(ids)
                    inicio = max(a.inicio for a in en_curso)
                    fin = min(a.fin for a in en_curso)
                    incidencias.append(Incidencia(
                        self.codigo,
                        f"Conflicto de capacidad en {recurso.id} (capacidad "
                        f"{recurso.capacidad}): {', '.join(ids)} se superponen",
                        ids, recurso.id,
                        f"Intervalo superpuesto: {fecha(inicio)} - {fecha(fin)}"))
        return incidencias


class CantidadRecursos(ReglaPorAsignacion):
    codigo, nombre = "R06", "Cantidad de recursos"

    def revisar(self, asignacion, actividad, plan, recursos, actividades):
        asignados = len(set(asignacion.recursos_ids))
        if asignados != actividad.cantidad_recursos:
            return [self.crear(f"Requiere {actividad.cantidad_recursos} recurso(s) "
                               f"y tiene {asignados}", asignacion)]
        return []


class DependenciasTerminadas(ReglaPorAsignacion):
    codigo, nombre = "R07", "Dependencias terminadas"

    def revisar(self, asignacion, actividad, plan, recursos, actividades):
        incidencias = []
        for dep_id in actividad.dependencias:
            # Una dependencia ya completada no necesita estar en la planificación.
            if getattr(actividades.get(dep_id), "estado", "") == "completada":
                continue
            dep = plan.asignacion_de(dep_id)
            if dep is None:
                incidencias.append(self.crear(
                    f"Depende de {dep_id}, que no está asignada ni completada", asignacion))
            elif dep.fin > asignacion.inicio:
                incidencias.append(self.crear(
                    f"Dependencia incumplida: comienza antes de que termine "
                    f"{dep_id} ({fecha(dep.fin)})", asignacion))
        return incidencias


class InicioPermitido(ReglaPorAsignacion):
    codigo, nombre = "R08", "Inicio permitido"

    def revisar(self, asignacion, actividad, plan, recursos, actividades):
        if asignacion.inicio < actividad.fecha_inicio:
            return [self.crear(f"Comienza antes de su inicio permitido "
                               f"({fecha(actividad.fecha_inicio)})", asignacion)]
        return []


class SinConflictosDeAsignacion(ReglaPorAsignacion):
    """Conflictos dentro del plan: actividad asignada más de una vez u
    horario que no coincide con la duración de la actividad."""
    codigo, nombre = "R09", "Inexistencia de conflictos"

    def revisar(self, asignacion, actividad, plan, recursos, actividades):
        incidencias = []
        veces = sum(1 for a in plan.asignaciones if a.actividad_id == actividad.id)
        if veces > 1 and plan.asignacion_de(actividad.id) is asignacion:
            incidencias.append(self.crear(f"La actividad está asignada {veces} veces", asignacion))
        diferencia = (asignacion.fin - asignacion.inicio) - timedelta(hours=actividad.duracion)
        if abs(diferencia) > timedelta(seconds=1):
            incidencias.append(self.crear(
                f"El horario dura {asignacion.duracion_horas:g} h y la actividad "
                f"requiere {actividad.duracion:g} h", asignacion))
        return incidencias


class SinCiclosDeDependencias(Regla):
    """Las dependencias no pueden formar ciclos (A002 -> A005 -> A002)."""
    codigo, nombre = "R10", "Dependencias sin ciclos"

    def evaluar(self, plan, recursos, actividades):
        grafo = {a.id: a.dependencias for a in actividades.values()}
        revisados = set()
        for inicio in sorted({a.actividad_id for a in plan.asignaciones}):
            ciclo = buscar_ciclo(grafo, inicio, [], revisados)
            if ciclo:
                return [Incidencia(self.codigo, "Ciclo de dependencias: " + " -> ".join(ciclo),
                                   tuple(sorted(set(ciclo))))]
        return []


def buscar_ciclo(grafo, nodo, camino, revisados):
    """Recorre las dependencias; si vuelve a una actividad del camino, hay ciclo."""
    if nodo in camino:
        return camino[camino.index(nodo):] + [nodo]
    if nodo not in revisados:
        for siguiente in sorted(grafo.get(nodo, [])):
            ciclo = buscar_ciclo(grafo, siguiente, camino + [nodo], revisados)
            if ciclo:
                return ciclo
        revisados.add(nodo)
    return None


def reglas_obligatorias() -> List[Regla]:
    return [IntegridadReferencias(), RecursoActivo(), HabilidadesCompatibles(),
            DisponibilidadCompleta(), CapacidadSimultanea(), CantidadRecursos(),
            DependenciasTerminadas(), InicioPermitido(), SinConflictosDeAsignacion(),
            SinCiclosDeDependencias()]


# PENALIZACIÓN POR RETRASO (no es restricción dura)

def calcular_retrasos(plan: Planificacion, actividades: Actividades) -> List[Retraso]:
    retrasos = []
    for a in plan.asignaciones:
        actividad = actividades.get(a.actividad_id)
        if actividad is not None and a.fin > actividad.fecha_limite:
            horas = (a.fin - actividad.fecha_limite).total_seconds() / 3600
            retrasos.append(Retraso(actividad.id, a.fin, actividad.fecha_limite, horas))
    return retrasos


# MOTOR

class MotorReglas:
    """Aplica las reglas a una planificación. No modifica ningún dato."""

    def __init__(self, reglas: Optional[List[Regla]] = None) -> None:
        self._reglas = list(reglas) if reglas is not None else reglas_obligatorias()

    @property
    def reglas(self) -> Tuple[Regla, ...]:
        return tuple(self._reglas)

    def agregar_regla(self, regla: Regla) -> None:
        if any(r.codigo == regla.codigo for r in self._reglas):
            raise ValueError(f"Ya existe una regla con el código {regla.codigo}")
        self._reglas.append(regla)

    def validar(self, plan: Planificacion, recursos: Recursos,
                actividades: Actividades) -> InformeValidacion:
        incidencias = [i for regla in self._reglas
                       for i in regla.evaluar(plan, recursos, actividades)]
        return InformeValidacion(plan.id, tuple(incidencias),
                                 tuple(calcular_retrasos(plan, actividades)))
