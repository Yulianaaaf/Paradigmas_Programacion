

from typing import Dict, List

from .modelos import (
    Actividad,
    PRIORIDADES,
    FORMATO_FECHA
)

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


# ACTIVIDADES ALMACENADAS EN MEMORIA

actividades: Dict[str, Actividad] = {}


# VALIDAR DEPENDENCIAS Y CICLOS

def validar_dependencias(
    identificador: str,
    dependencias: List[str]
) -> bool:

    # Verificar que las dependencias existan.
    for dependencia in dependencias:

        if dependencia == identificador:
            print(
                f"Error: la actividad {identificador} "
                "no puede depender de sí misma."
            )
            return False

        if dependencia not in actividades:
            print(
                f"Error: la actividad {dependencia} no existe."
            )
            return False

    # Construir el grafo de dependencias.
    grafo = {
        id_actividad: actividad.dependencias.copy()
        for id_actividad, actividad in actividades.items()
    }

    # Incorporar las nuevas dependencias.
    grafo[identificador] = dependencias.copy()

    visitados = set()
    en_proceso = set()
    camino = []

    def detectar_ciclo(nodo):

        if nodo in en_proceso:

            inicio_ciclo = camino.index(nodo)
            ciclo = camino[inicio_ciclo:] + [nodo]

            print(
                "Error: se detectó un ciclo de dependencias: "
                + " -> ".join(ciclo)
            )

            return True

        if nodo in visitados:
            return False

        en_proceso.add(nodo)
        camino.append(nodo)

        for dependencia in grafo.get(nodo, []):

            if detectar_ciclo(dependencia):
                return True

        camino.pop()
        en_proceso.remove(nodo)
        visitados.add(nodo)

        return False

    # Revisar todos los nodos del grafo.
    for nodo in grafo:

        if detectar_ciclo(nodo):
            return False

    return True


# CAPTURAR DATOS

def capturar_datos_actividad(
    id_actual: str = ""
) -> Actividad:

    print("\nINGRESAR DATOS DE LA ACTIVIDAD")

    # IDENTIFICADOR

    if id_actual:
        identificador = id_actual

        print(
            f"ID de la actividad: {identificador} "
            "(no editable)"
        )

    else:

        while True:

            identificador = leer_texto(
                "ID de la actividad: "
            ).upper()

            if identificador not in actividades:
                break

            print(
                "Error: ID duplicado. Ya existe esa actividad."
            )

    # DESCRIPCIÓN

    descripcion = leer_texto(
        "Descripción: "
    )

    # DURACIÓN

    duracion = leer_decimal(
        "Duración en horas (mayor a 0): ",
        0.000001
    )

    # PRIORIDAD

    prioridad = leer_opcion_lista(
        "Prioridad",
        PRIORIDADES
    )

    # VENTANA TEMPORAL

    while True:

        fecha_inicio = leer_fecha(
            "Fecha de inicio (AAAA-MM-DD HH:MM): "
        )

        fecha_limite = leer_fecha(
            "Fecha límite (AAAA-MM-DD HH:MM): "
        )

        if fecha_inicio < fecha_limite:
            break

        print(
            "Error: la fecha de inicio debe ser "
            "anterior a la fecha límite."
        )

    # HABILIDADES

    habilidades = leer_lista(
        "Habilidades requeridas separadas por comas: "
    )

    # CANTIDAD DE RECURSOS

    cantidad_recursos = leer_entero(
        "Cantidad de recursos necesarios: ",
        1
    )

    # DEPENDENCIAS

    print(
        "\nIngresá los IDs de las actividades "
        "de las que depende."
    )

    print(
        "Si no tiene dependencias, escribí NINGUNA."
    )

    while True:

        texto_dependencias = input(
            "Dependencias: "
        ).strip().upper()

        if texto_dependencias == "NINGUNA":

            dependencias = []

        else:

            dependencias = [
                elemento.strip()
                for elemento in texto_dependencias.split(",")
                if elemento.strip()
            ]

            if not dependencias:

                print(
                    "Error: ingresá IDs válidos o NINGUNA."
                )
                continue

            if len(dependencias) != len(set(dependencias)):

                print(
                    "Error: no podés repetir una dependencia."
                )
                continue

        # Validar referencias y ciclos.
        if validar_dependencias(
            identificador,
            dependencias
        ):
            break

        print(
            "No se pudieron validar las dependencias. "
            "Ingresá nuevamente las dependencias."
        )

    # CONSERVAR EL ESTADO ACTUAL AL EDITAR

    estado = "pendiente"

    if id_actual and id_actual in actividades:
        estado = actividades[id_actual].estado

    # CREAR OBJETO ACTIVIDAD

    return Actividad(
        id=identificador,
        descripcion=descripcion,
        duracion=duracion,
        prioridad=prioridad,
        fecha_inicio=fecha_inicio,
        fecha_limite=fecha_limite,
        habilidades=habilidades,
        cantidad_recursos=cantidad_recursos,
        dependencias=dependencias,
        estado=estado
    )


# MOSTRAR ACTIVIDAD

def mostrar_actividad(actividad: Actividad) -> None:

    print("\n" + "-" * 50)

    print(f"ID: {actividad.id}")
    print(f"Descripción: {actividad.descripcion}")
    print(f"Duración: {actividad.duracion} horas")
    print(f"Prioridad: {actividad.prioridad}")

    print(
        "Fecha de inicio:",
        actividad.fecha_inicio.strftime(FORMATO_FECHA)
    )

    print(
        "Fecha límite:",
        actividad.fecha_limite.strftime(FORMATO_FECHA)
    )

    print(
        f"Habilidades: {', '.join(actividad.habilidades)}"
    )

    print(
        f"Cantidad de recursos: {actividad.cantidad_recursos}"
    )

    if actividad.dependencias:

        print(
            f"Dependencias: {', '.join(actividad.dependencias)}"
        )

    else:

        print("Dependencias: Ninguna")

    print(f"Estado: {actividad.estado}")


# REGISTRAR ACTIVIDAD

def registrar_actividad() -> None:

    actividad = capturar_datos_actividad()

    actividades[actividad.id] = actividad

    print(
        f"\nActividad {actividad.id} "
        "registrada correctamente."
    )


# LISTAR ACTIVIDADES

def listar_actividades() -> None:

    if not actividades:

        print("\nNo hay actividades registradas.")
        return

    print("\nLISTADO DE ACTIVIDADES")

    for actividad in actividades.values():

        mostrar_actividad(actividad)


# CONSULTAR ACTIVIDAD

def consultar_actividad() -> None:

    identificador = leer_texto(
        "Ingresá el ID de la actividad: "
    ).upper()

    actividad = actividades.get(identificador)

    if actividad is None:

        print("No existe una actividad con ese ID.")
        return

    mostrar_actividad(actividad)


# EDITAR ACTIVIDAD

def editar_actividad() -> None:

    identificador = leer_texto(
        "ID de la actividad que querés editar: "
    ).upper()

    actividad_anterior = actividades.get(identificador)

    if actividad_anterior is None:

        print("No existe una actividad con ese ID.")
        return

    print("\nDATOS ACTUALES")

    mostrar_actividad(actividad_anterior)

    print("\nINGRESÁ LOS NUEVOS DATOS")

    actividad_nueva = capturar_datos_actividad(
        id_actual=identificador
    )

    # Actualizar únicamente cuando los datos son válidos.
    actividades[identificador] = actividad_nueva

    print(
        f"Actividad {identificador} "
        "actualizada correctamente."
    )


# ELIMINAR ACTIVIDAD PENDIENTE

def eliminar_actividad() -> None:

    identificador = leer_texto(
        "ID de la actividad que querés eliminar: "
    ).upper()

    actividad = actividades.get(identificador)

    if actividad is None:

        print("No existe una actividad con ese ID.")
        return

    # Verificar que esté pendiente.
    if actividad.estado != "pendiente":

        print(
            "Error: solo se pueden eliminar "
            "actividades pendientes."
        )
        return

    # Revisar si otras actividades dependen de esta.
    dependientes = [
        otra.id
        for otra in actividades.values()
        if identificador in otra.dependencias
    ]

    if dependientes:

        print(
            "Error: no se puede eliminar la actividad "
            f"{identificador}."
        )

        print(
            "Las siguientes actividades dependen de ella: "
            + ", ".join(dependientes)
        )

        print(
            "Primero resolvé las dependencias."
        )

        return

    # Confirmar eliminación.
    if confirmar(
        f"¿Deseás eliminar la actividad {identificador}?"
    ):

        del actividades[identificador]

        print(
            f"Actividad {identificador} "
            "eliminada correctamente."
        )


# MENÚ DE ACTIVIDADES

def menu_actividades() -> None:

    while True:

        print("\n========== RF-02: ACTIVIDADES ==========")

        print("1. Registrar actividad")
        print("2. Listar actividades")
        print("3. Consultar actividad")
        print("4. Editar actividad")
        print("5. Eliminar actividad pendiente")
        print("0. Volver al menú principal")

        opcion = input(
            "Elegí una opción: "
        ).strip()

        if opcion == "1":

            registrar_actividad()
            pausar()

        elif opcion == "2":

            listar_actividades()
            pausar()

        elif opcion == "3":

            consultar_actividad()
            pausar()

        elif opcion == "4":

            editar_actividad()
            pausar()

        elif opcion == "5":

            eliminar_actividad()
            pausar()

        elif opcion == "0":

            print("Saliendo del RF-02...")
            break

        else:

            print("Opción inválida.")
            pausar()


if __name__ == "__main__":

    menu_actividades()
