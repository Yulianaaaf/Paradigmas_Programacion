
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



# CONFIGURACIÓN DEL RF-02

PRIORIDADES = [
    "baja",
    "media",
    "alta",
    "critica"
]

ESTADOS_ACTIVIDAD = [
    "pendiente",
    "en_progreso",
    "completada"
]


@dataclass
class Actividad:
    id: str
    descripcion: str
    duracion: float
    prioridad: str
    fecha_inicio: datetime
    fecha_limite: datetime
    habilidades: List[str]
    cantidad_recursos: int
    dependencias: List[str]
    estado: str = "pendiente"
