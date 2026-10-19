

from typing import Dict

from .modelos import Recurso, TIPOS_RECURSO, FORMATO_FECHA

from .funciones import (
    leer_texto,
    leer_entero,
    leer_decimal,
    leer_fecha,
    leer_lista,
    leer_opcion_lista,
    confirmar,
    pausar
)


# Recursos almacenados en memoria.
recursos: Dict[str, Recurso] = {}


# CAPTURAR DATOS

def capturar_datos_recurso(id_actual: str = "") -> Recurso:
    print("\nINGRESAR DATOS DEL RECURSO")

    while True:
        identificador = leer_texto("ID del recurso: ").upper()

        if identificador not in recursos or identificador == id_actual:
            break

        print("Error: ID duplicado. Ya existe ese recurso.")

    nombre = leer_texto("Nombre: ")

    tipo = leer_opcion_lista(
        "Tipo de recurso",
        TIPOS_RECURSO
    )

    habilidades = leer_lista(
        "Habilidades separadas por comas: "
    )

    capacidad = leer_entero(
        "Capacidad (entero mayor o igual a 1): ",
        1
    )

    costo_hora = leer_decimal(
        "Costo por hora (mayor o igual a 0): ",
        0
    )

    while True:
        inicio = leer_fecha(
            "Inicio de disponibilidad (AAAA-MM-DD HH:MM): "
        )

        fin = leer_fecha(
            "Fin de disponibilidad (AAAA-MM-DD HH:MM): "
        )

        if inicio < fin:
            break

        print("Error: el inicio debe ser anterior al fin.")

    activo = True

    if id_actual and id_actual in recursos:
        activo = recursos[id_actual].activo

    return Recurso(
        id=identificador,
        nombre=nombre,
        tipo=tipo,
        habilidades=habilidades,
        capacidad=capacidad,
        costo_hora=costo_hora,
        disponibilidad_inicio=inicio,
        disponibilidad_fin=fin,
        activo=activo
    )


# MOSTRAR RECURSO

def mostrar_recurso(recurso: Recurso) -> None:
    estado = "Activo" if recurso.activo else "Inactivo"

    print("\n" + "-" * 45)
    print(f"ID: {recurso.id}")
    print(f"Nombre: {recurso.nombre}")
    print(f"Tipo: {recurso.tipo}")
    print(f"Habilidades: {', '.join(recurso.habilidades)}")
    print(f"Capacidad: {recurso.capacidad}")
    print(f"Costo por hora: {recurso.costo_hora:.2f}")

    print(
        "Disponible desde:",
        recurso.disponibilidad_inicio.strftime(FORMATO_FECHA)
    )

    print(
        "Disponible hasta:",
        recurso.disponibilidad_fin.strftime(FORMATO_FECHA)
    )

    print(f"Estado: {estado}")


# REGISTRAR RECURSO

def registrar_recurso() -> None:
    recurso = capturar_datos_recurso()
    recursos[recurso.id] = recurso

    print(f"\nRecurso {recurso.id} registrado correctamente.")


# LISTAR RECURSOS

def listar_recursos() -> None:
    if not recursos:
        print("\nNo hay recursos registrados.")
        return

    print("\nLISTADO DE RECURSOS")

    for recurso in recursos.values():
        mostrar_recurso(recurso)


# CONSULTAR RECURSO

def consultar_recurso() -> None:
    identificador = leer_texto(
        "Ingresá el ID del recurso: "
    ).upper()

    recurso = recursos.get(identificador)

    if recurso is None:
        print("No existe un recurso con ese ID.")
        return

    mostrar_recurso(recurso)


# EDITAR RECURSO

def editar_recurso() -> None:
    identificador = leer_texto(
        "ID del recurso que querés editar: "
    ).upper()

    recurso_anterior = recursos.get(identificador)

    if recurso_anterior is None:
        print("No existe un recurso con ese ID.")
        return

    print("\nDATOS ACTUALES")
    mostrar_recurso(recurso_anterior)

    print("\nINGRESÁ LOS NUEVOS DATOS")

    recurso_nuevo = capturar_datos_recurso(
        id_actual=identificador
    )

    del recursos[identificador]
    recursos[recurso_nuevo.id] = recurso_nuevo

    print("Recurso actualizado correctamente.")


# DESACTIVAR RECURSO

def desactivar_recurso() -> None:
    identificador = leer_texto(
        "ID del recurso que querés desactivar: "
    ).upper()

    recurso = recursos.get(identificador)

    if recurso is None:
        print("No existe un recurso con ese ID.")
        return

    if not recurso.activo:
        print("El recurso ya está inactivo.")
        return

    if confirmar(
        f"¿Deseás desactivar el recurso {identificador}?"
    ):
        recurso.activo = False

        print(
            "Recurso desactivado correctamente. "
            "El registro se conserva."
        )


# MENÚ DE RECURSOS

def menu_recursos() -> None:
    while True:
        print("\n========== RF-01: RECURSOS ==========")
        print("1. Registrar recurso")
        print("2. Listar recursos")
        print("3. Consultar recurso")
        print("4. Editar recurso")
        print("5. Desactivar recurso")
        print("0. Volver al menú principal")

        opcion = input("Elegí una opción: ").strip()

        if opcion == "1":
            registrar_recurso()
            pausar()

        elif opcion == "2":
            listar_recursos()
            pausar()

        elif opcion == "3":
            consultar_recurso()
            pausar()

        elif opcion == "4":
            editar_recurso()
            pausar()

        elif opcion == "5":
            desactivar_recurso()
            pausar()

        elif opcion == "0":
            print("Saliendo del RF-01...")
            break

        else:
            print("Opción inválida.")
            pausar()


if __name__ == "__main__":
    menu_recursos()
