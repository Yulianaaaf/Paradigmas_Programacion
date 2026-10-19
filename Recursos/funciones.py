
from datetime import datetime
from typing import List

from .modelos import FORMATO_FECHA


def leer_texto(mensaje: str) -> str:
    while True:
        valor = input(mensaje).strip()

        if valor:
            return valor

        print("Error: este campo no puede estar vacío.")


def leer_entero(mensaje: str, minimo: int = 1) -> int:
    while True:
        try:
            valor = int(input(mensaje).strip())

            if valor < minimo:
                print(
                    f"Error: el valor mínimo permitido es {minimo}."
                )
                continue

            return valor

        except ValueError:
            print("Error: ingresá un número entero válido.")


def leer_decimal(mensaje: str, minimo: float = 0) -> float:
    while True:
        try:
            texto = input(mensaje).strip().replace(",", ".")
            valor = float(texto)

            if valor < minimo:
                print(
                    f"Error: el valor mínimo permitido es {minimo}."
                )
                continue

            return valor

        except ValueError:
            print("Error: ingresá un número válido.")


def leer_fecha(mensaje: str) -> datetime:
    while True:
        texto = input(mensaje).strip()

        try:
            return datetime.strptime(texto, FORMATO_FECHA)

        except ValueError:
            print("Fecha inválida.")
            print("Usá el formato AAAA-MM-DD HH:MM.")
            print("Ejemplo: 2026-10-20 08:00")


def leer_lista(mensaje: str) -> List[str]:
    while True:
        texto = input(mensaje).strip()

        elementos = [
            elemento.strip()
            for elemento in texto.split(",")
            if elemento.strip()
        ]

        if elementos:
            return elementos

        print("Error: ingresá al menos un elemento.")


def leer_opcion_lista(
    mensaje: str,
    opciones: List[str]
) -> str:
    opciones_texto = ", ".join(opciones)

    while True:
        valor = input(
            f"{mensaje} ({opciones_texto}): "
        ).strip().lower()

        if valor in opciones:
            return valor

        print(f"Opciones permitidas: {opciones_texto}.")


def confirmar(mensaje: str) -> bool:
    while True:
        respuesta = input(
            f"{mensaje} (s/n): "
        ).strip().lower()

        if respuesta in ("s", "si", "sí"):
            return True

        if respuesta in ("n", "no"):
            return False

        print("Respondé s o n.")


def pausar() -> None:
    input("\nPresioná Enter para continuar...")
