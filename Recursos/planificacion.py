
"""Asignación y planificación.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Tuple
from .modelos import FORMATO_FECHA


@dataclass(frozen=True)
class Asignacion:
    actividad_id: str
    recursos_ids: Tuple[str, ...]
    inicio: datetime
    fin: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "recursos_ids", tuple(self.recursos_ids))

        if self.inicio >= self.fin:
            raise ValueError("asignacion: el inicio debe ser anterior al fin")

    @property
    def duracion_horas(self) -> float:
        return (self.fin - self.inicio).total_seconds() / 3600

    def horario(self) -> str:
        return (
            f"{self.inicio.strftime(FORMATO_FECHA)} - "
            f"{self.fin.strftime(FORMATO_FECHA)}"
        )


@dataclass(frozen=True)
class Planificacion:
    id: str
    asignaciones: Tuple[Asignacion, ...] = ()
    algoritmo: str = ""

    pendientes: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "asignaciones", tuple(self.asignaciones))

    def asignacion_de(self, actividad_id: str) -> Optional[Asignacion]:
        """Devuelve la asignación de una actividad, o None si no está asignada."""
        for asignacion in self.asignaciones:
            if asignacion.actividad_id == actividad_id:
                return asignacion
        return None
