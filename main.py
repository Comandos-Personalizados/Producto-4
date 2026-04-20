import os
import sys
import funciones_red

def mostrar_menu():
    """
    Función para mostrar el menú principal de la aplicación.
    Limpia la pantalla antes de mostrar las opciones para mantener una consola limpia.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("========================================")
    print("      OPTIMIZADOR DE CONEXIÓN DNS       ")
    print("              Producto 3                ")
    print("========================================")
    print("1. Resolución de dominios (Punto 4 del menú)")
    print("2. Exportar configuración local (Punto 5 del menú)")
    print("3. Selección de adaptador y DNS actual (Puntos 6 y 7 del menú)")
    print("4. Benchmarking de DNS y modificación (Punto 8 y 9 del menú)")
    print("5. Salir")
    print("========================================")

def main():
    """
    Función principal que maneja el bucle del programa (while True).
    Lee la opción elegida por el usuario y ejecuta la acción correspondiente.
    """
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\nElige una opción (1-5): ")
            
            if opcion == '1':
                print("\nOpción 1 seleccionada. La lógica estará en funciones_red.py.")
                input("\nPresiona ENTER para continuar...")
                
            elif opcion == '2':
                print("\nOpción 2 seleccionada. La lógica estará en funciones_red.py.")
                input("\nPresiona ENTER para continuar...")
                
            elif opcion == '3':
                print("\nOpción 3 seleccionada. La lógica estará en funciones_red.py.")
                input("\nPresiona ENTER para continuar...")
                
            elif opcion == '4':
                print("\nOpción 4 seleccionada. La lógica estará en funciones_red.py.")
                input("\nPresiona ENTER para continuar...")
                
            elif opcion == '5':
                print("\nSaliendo del optimizador. ¡Hasta pronto!")
                sys.exit(0)
                
            else:
                print("\n[!] Opción no válida. Por favor, selecciona un número entre 1 y 5.")
                input("\nPresiona ENTER para continuar...")
        
        except KeyboardInterrupt:
            # Captura si el usuario presiona Ctrl+C en la consola
            print("\n\nSaliendo de forma segura...")
            sys.exit(0)
        except Exception as e:
            # Captura cualquier otro error imprevisto
            print(f"\n[!] Ha ocurrido un error inesperado: {str(e)}")
            input("\nPresiona ENTER para continuar...")

if __name__ == "__main__":
    main()
