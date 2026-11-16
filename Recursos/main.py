from .recursos import menu_recursos
from .actividad import menu_actividades
from .funciones import pausar                       # CAMBIO (nuevo)
from .menu_planificacion import (                   # CAMBIO (nuevo)
    ejecutar_algoritmo_inicial,
    validar_planificacion,
    cargar_datos_demo
)
from .menu_analisis import (
    menu_analisis_funcional,
    menu_comparar_paralelo
)


def main():

    while True:

        print("\n========== SISTEMA DE PLANIFICACIÓN ==========")

        print("1. Gestión de recursos (RF-01)")
        print("2. Gestión de actividades (RF-02)")
        print("3. Ejecutar algoritmo inicial (RF-04)")  # CAMBIO (nuevo)
        print("4. Validar planificación (RF-03)")       # CAMBIO (nuevo)
        print("5. Cargar datos de demostración")         # CAMBIO (nuevo)
        print("6. Análisis funcional (RF-06)")
        print("7. Comparar secuencial y paralelo (RF-07)")
        print("0. Salir")

        opcion = input("Elegí una opción: ").strip()

        if opcion == "1":
            menu_recursos()

        elif opcion == "2":
            menu_actividades()

        elif opcion == "3":                              # CAMBIO (nuevo)
            ejecutar_algoritmo_inicial()
            pausar()

        elif opcion == "4":                              # CAMBIO (nuevo)
            validar_planificacion()
            pausar()

        elif opcion == "5":                              # CAMBIO (nuevo)
            cargar_datos_demo()
            pausar()

        elif opcion == "6":
            menu_analisis_funcional()

        elif opcion == "7":
            menu_comparar_paralelo()

        elif opcion == "0":
            print("Saliendo del sistema...")
            break

        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()
