import socket
import os
import subprocess
import re

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

def evaluar_y_modificar_dns():
    """
    Paso 5 y 6: Realiza un ping a los servidores DNS y verifica cuál es el más rápido.
    En caso de empate, usa tracert para contar los saltos.
    Finalmente, si el servidor más rápido es distinto al actual, lo modifica usando netsh.
    """
    print("\n--- BENCHMARKING DE DNS Y MODIFICACIÓN ---")
    
    # Nombre del adaptador
    nombre_adaptador = input("Introduce el Nombre del adaptador a configurar (ej. 'Wi-Fi' o 'Ethernet'): ").strip()
    if not nombre_adaptador:
        print("[!] Nombre de adaptador vacío. Operación cancelada.")
        return

    # DNS actual
    dns_actual = input("Introduce la IP del DNS ACTUAL del adaptador (para comparar): ").strip()
    
    ips = []
    if dns_actual:
        ips.append(dns_actual)
        
    # Leer archivo DNSips.txt
    ruta_dns = input("Introduce la ruta del archivo con IPs de DNS (ej. DNSips.txt): ").strip()
    if os.path.isfile(ruta_dns):
        try:
            with open(ruta_dns, 'r', encoding='utf-8') as f:
                for linea in f:
                    ip = linea.strip()
                    if ip and ip not in ips:
                        ips.append(ip)
        except Exception as e:
            print(f"\n[!] Error leyendo el archivo de DNS: {e}")
    else:
        print(f"\n[!] Archivo '{ruta_dns}' no encontrado. Se usarán solo las IPs manuales (si las hay).")

    if not ips:
        print("\n[!] No hay IPs de DNS para evaluar. Operación cancelada.")
        return

    print("\nIniciando ping a los servidores DNS...\n")
    resultados = []

    for ip in ips:
        print(f"Haciendo ping a {ip}...")
        try:
            # Comando ping para Windows (-n 4) y para Linux (-c 4)
            cmd_ping = ['ping', '-n', '4', ip] if os.name == 'nt' else ['ping', '-c', '4', ip]
            res_ping = subprocess.run(cmd_ping, capture_output=True, text=True)
            
            tiempo_medio = float('inf')
            
            if res_ping.returncode == 0:
                # Regex para extraer el tiempo medio en Windows (Media = Xms / Average = Xms)
                match_win = re.search(r'(?:Media|Average) = (\d+)ms', res_ping.stdout, re.IGNORECASE)
                # Regex simplificado para Linux (min/avg/max/mdev = X/Y/Z/W ms)
                match_lin = re.search(r'mdev = [\d.]+/(.*?)/[\d.]+/', res_ping.stdout)
                
                if match_win:
                    tiempo_medio = float(match_win.group(1))
                elif match_lin:
                    try:
                        tiempo_medio = float(match_lin.group(1))
                    except ValueError:
                        pass
                
                # Caso extremo donde sí responde pero por otro formato
                if tiempo_medio == float('inf'):
                    # Si no encuentra formato, asigna un valor penalizado pero válido
                    tiempo_medio = 999.0 

            resultados.append({'ip': ip, 'tiempo': tiempo_medio, 'saltos': float('inf')})
            if tiempo_medio != float('inf') and tiempo_medio != 999.0:
                print(f"Tiempo medio para {ip}: {tiempo_medio} ms")
            else:
                print(f"Ping completado (Tiempo desconocido o muy alto) para {ip}.")
            
        except Exception as e:
            print(f"Error evaluando ping para {ip}: {e}")
            resultados.append({'ip': ip, 'tiempo': float('inf'), 'saltos': float('inf')})

    if not resultados:
        return

    # Buscar el DNS ganador ordenando por tiempo
    resultados.sort(key=lambda x: x['tiempo'])
    mejor_tiempo = resultados[0]['tiempo']
    
    # Evaluar empates
    empates = [r for r in resultados if r['tiempo'] == mejor_tiempo]
    
    if len(empates) > 1 and mejor_tiempo != float('inf'):
        print(f"\n[i] Empate encontrado con tiempo {mejor_tiempo} ms. Realizando tracert para desempate...\n")
        for r in empates:
            ip = r['ip']
            print(f"Trazando ruta a {ip} (máx 15 saltos)...")
            try:
                cmd_tr = ['tracert', '-d', '-h', '15', ip] if os.name == 'nt' else ['traceroute', '-n', '-m', '15', ip]
                res_tr = subprocess.run(cmd_tr, capture_output=True, text=True)
                
                saltos = 0
                for linea in res_tr.stdout.split('\n'):
                    linea = linea.strip()
                    # Contamos las líneas que empiezan con un número de salto
                    if re.match(r'^\d+', linea):
                        saltos += 1
                        
                r['saltos'] = saltos
                print(f"Saltos contabilizados para {ip}: {saltos}")
            except Exception as e:
                print(f"Error trazando {ip}: {e}")
                
        # Re-ordenamos solo los empatados por saltos
        empates.sort(key=lambda x: x['saltos'])
        ganador = empates[0]
    else:
        ganador = resultados[0]

    # Re-ordenar ranking global para mostrar (Prioridad: Tiempo, luego Saltos)
    resultados.sort(key=lambda x: (x['tiempo'], x['saltos']))
    
    print("\n" + "="*30)
    print("      RANKING FINAL DNS   ")
    print("="*30)
    for i, r in enumerate(resultados):
        str_saltos = str(r['saltos']) if r['saltos'] != float('inf') else 'N/A'
        str_tiempo = f"{r['tiempo']} ms" if r['tiempo'] != float('inf') else 'Inalcanzable'
        print(f"{i+1}º - IP: {r['ip']} | Tiempo media: {str_tiempo} | Saltos: {str_saltos}")
        
    ip_ganadora = ganador['ip']
    print(f"\n[+] EL DNS GANADOR ES: {ip_ganadora}")

    # Paso 6: Modificación del adaptador
    if ip_ganadora == dns_actual:
        print("\nEl DNS actual ya es el más rápido. No se realizan cambios.")
    else:
        print(f"\n[i] Cambiando DNS del adaptador '{nombre_adaptador}' a {ip_ganadora}... (Requiere Administrador)")
        if os.name == 'nt':
            try:
                # netsh interface ipv4 set dnsservers name="NombreAdaptador" static <IP_Ganadora> primary
                comando_dns = [
                    'netsh', 'interface', 'ipv4', 'set', 'dnsservers',
                    f'name={nombre_adaptador}', 'static', ip_ganadora, 'primary'
                ]
                res_dns = subprocess.run(comando_dns, capture_output=True, text=True)
                
                if res_dns.returncode == 0:
                    print("\n¡Cambio de DNS exitoso! Ahora posees el servidor DNS más rápido configurado.")
                else:
                    print("\n[!] Error al cambiar el DNS. ¿Aseguraste ejecutar el programa como Administrador?")
                    print(f"Detalle técnico: {res_dns.stderr.strip() or res_dns.stdout.strip()}")
            except Exception as e:
                print(f"\n[!] Error inesperado al ejecutar netsh: {e}")
        else:
            print("\n[!] El cambio automático con 'netsh' solo está soportado en sistemas Windows.")
