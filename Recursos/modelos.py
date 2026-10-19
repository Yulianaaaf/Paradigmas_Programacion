
from dataclasses import dataclass
from datetime import datetime
from typing import List


FORMATO_FECHA = "%Y-%m-%d %H:%M"

TIPOS_RECURSO = [
    "humano",
    "material",
    "tecnologico"
]


@dataclass
class Recurso:
    id: str
    nombre: str
    tipo: str
    habilidades: List[str]
    capacidad: int
    costo_hora: float
    disponibilidad_inicio: datetime
    disponibilidad_fin: datetime
    activo: bool = True
