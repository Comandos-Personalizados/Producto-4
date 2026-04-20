import socket
import os

def resolucion_dominios():
    """
    Pide al usuario la ruta del archivo de texto con los dominios,
    lee los dominios de cada línea y usa la librería socket para resolver
    y mostrar por pantalla la dirección IP asociada a cada uno.
    """
    print("\n--- RESOLUCIÓN DE DOMINIOS ---")
    ruta_archivo = input("Introduce la ruta del archivo de dominios (ej. web.txt): ")
    
    # Verificamos si la ruta es correcta y el archivo existe
    if not os.path.isfile(ruta_archivo):
        print(f"\n[!] Error: El archivo '{ruta_archivo}' no existe o la ruta es incorrecta.")
        return

    try:
        # Abrimos el archivo en modo lectura
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            lineas = archivo.readlines()
            
            # Si el archivo está vacío
            if not lineas:
                print("El archivo está vacío.")
                return
                
            print("\nDominios encontrados y sus IPs resueltas:")
            print("-" * 50)
            
            # Recorremos cada línea del archivo
            for linea in lineas:
                # Limpiamos los espacios y retornos de carro
                dominio = linea.strip()
                
                # Omitimos líneas vacías si las hay
                if not dominio:
                    continue
                    
                print(f"Resolviendo: {dominio} ...", end=" ")
                
                try:
                    # Intentamos resolver el dominio con socket.gethostbyname
                    ip = socket.gethostbyname(dominio)
                    print(f"IP: {ip}")
                except socket.gaierror as e:
                    # Capturamos el error si no se pudo resolver el host
                    print(f"Error al resolver. No se pudo obtener IP.")
                except Exception as e:
                    # Capturamos cualquier otro error durante la resolución
                    print(f"Error inesperado: {str(e)}")
                    
    except PermissionError:
        print("\n[!] Error de permisos al intentar leer el archivo.")
    except Exception as e:
        print(f"\n[!] Ocurrió un error inesperado al leer el archivo: {str(e)}")
