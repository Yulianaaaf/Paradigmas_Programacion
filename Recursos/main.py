
from .recursos import menu_recursos
from .actividad import menu_actividades


def main():

    while True:

        print("\n========== SISTEMA DE PLANIFICACIÓN ==========")

        print("1. Gestión de recursos (RF-01)")
        print("2. Gestión de actividades (RF-02)")
        print("0. Salir")

        opcion = input("Elegí una opción: ").strip()

        if opcion == "1":
            menu_recursos()

        elif opcion == "2":
            menu_actividades()

        elif opcion == "0":
            print("Saliendo del sistema...")
            break

        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()
