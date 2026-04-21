import socket
import os
import subprocess

def exportar_configuracion_local():
    """
    Ejecuta el comando de Windows 'ipconfig /all' mediante subprocess,
    captura su salida y la guarda en el archivo 'configuracionlocal.txt'.
    """
    print("\n--- EXPORTAR CONFIGURACIÓN LOCAL ---")
    
    try:
        # Ejecutamos ipconfig /all, capturando la salida (stdout)
        # Usamos check=True para que lance una excepción si el comando falla
        # text=True decodifica la salida como string usando la codificación por defecto
        resultado = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, check=True)
        
        # Abrimos el archivo en modo escritura 'w'
        with open('configuracionlocal.txt', 'w', encoding='utf-8') as archivo:
            # Escribimos toda la salida estándar del comando en el archivo
            archivo.write(resultado.stdout)
            
        print("\n¡Éxito! La configuración de red se ha exportado correctamente a 'configuracionlocal.txt'.")
        
    except FileNotFoundError:
        # Esto ocurre si el comando 'ipconfig' no se encuentra (por ejemplo, si no estamos en Windows)
        print("\n[!] Error: El comando 'ipconfig' no está disponible en este sistema.")
    except subprocess.CalledProcessError as e:
        # Ocurre si el comando se ejecuta pero devuelve un código de error
        print(f"\n[!] Error en la ejecución del comando: {e}")
    except PermissionError:
        print("\n[!] Error de permisos al intentar escribir en 'configuracionlocal.txt'.")
    except Exception as e:
        print(f"\n[!] Ocurrió un error inesperado al exportar la configuración: {str(e)}")

def seleccion_adaptador():
    """
    Extrae y muestra los adaptadores de red activos utilizando netsh.
    Permite al usuario elegir un adaptador y muestra su servidor DNS actual.
    """
    print("\n--- SELECCIÓN DE ADAPTADOR Y DNS ACTUAL ---")
    
    try:
        # Ejecutamos el comando para mostrar los interfaces
        resultado = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
            capture_output=True, text=True, check=True
        )
        
        print("\nAdaptadores de red disponibles:\n")
        # Mostramos la salida original para que el usuario vea los nombres
        print(resultado.stdout)
        
        # Solicitamos al usuario que escriba manualmente el nombre del adaptador
        nombre_adaptador = input("Introduce el Nombre del adaptador tal como aparece arriba (ej. 'Wi-Fi' o 'Ethernet'): ").strip()
        
        if not nombre_adaptador:
            print("\n[!] Error: No has introducido ningún nombre de adaptador.")
            return
            
        print(f"\nObteniendo configuración DNS actual para el adaptador: '{nombre_adaptador}'...\n")
        
        # Ejecutamos el comando para extraer los servidores DNS del adaptador elegido
        # Se proporciona el argumento name=<Nombre> para acotar la búsqueda al específico
        resultado_dns = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'dnsservers', f'name={nombre_adaptador}'],
            capture_output=True, text=True, check=True
        )
        
        # Imprimimos la salida con la información del DNS actual
        print(resultado_dns.stdout)
        
    except FileNotFoundError:
        print("\n[!] Error: El comando 'netsh' no está disponible en este sistema (es exclusivo de Windows).")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error al ejecutar comando de red. ¿El nombre del adaptador '{nombre_adaptador}' es correcto?")
    except Exception as e:
        print(f"\n[!] Ocurrió un error inesperado: {str(e)}")

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
