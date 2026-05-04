"""Punto de entrada de la aplicación.

Muestra el menú principal y delega cada opción en la función correspondiente
de la librería funciones_red. La opción 5 (Producto 4) genera un archivo XML
con la información de red del adaptador seleccionado.
"""

import os
import sys
import funciones_red


def mostrar_menu():
    """Limpia la pantalla y dibuja el menú principal."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("========================================")
    print("      Optimizador de conexión DNS       ")
    print("              Producto 4                ")
    print("========================================")
    print("1. Resolución de dominios")
    print("2. Exportar configuración local")
    print("3. Selección de adaptador y DNS actual")
    print("4. Benchmarking de DNS y modificación")
    print("5. Generar archivo XML del adaptador")
    print("6. Salir")
    print("========================================")

def main():
    """Bucle principal: muestra el menú, lee la opción y ejecuta la acción."""
    while True:
        mostrar_menu()

        try:
            opcion = input("\nElige una opción (1-6): ")

            if opcion == '1':
                funciones_red.resolucion_dominios()
                input("\nPulsa ENTER para continuar...")

            elif opcion == '2':
                funciones_red.exportar_configuracion_local()
                input("\nPulsa ENTER para continuar...")

            elif opcion == '3':
                funciones_red.seleccion_adaptador()
                input("\nPulsa ENTER para continuar...")

            elif opcion == '4':
                funciones_red.evaluar_y_modificar_dns()
                input("\nPulsa ENTER para continuar...")

            elif opcion == '5':
                funciones_red.generar_xml_adaptador()
                input("\nPulsa ENTER para continuar...")

            elif opcion == '6':
                print("\nSaliendo.")
                sys.exit(0)

            else:
                print("\n[!] Opción no válida. Introduce un número del 1 al 6.")
                input("\nPulsa ENTER para continuar...")

        except KeyboardInterrupt:
            print("\n\nInterrumpido por el usuario. Saliendo.")
            sys.exit(0)
        except Exception as e:
            print(f"\n[!] Error inesperado: {str(e)}")
            input("\nPulsa ENTER para continuar...")

if __name__ == "__main__":
    main()
