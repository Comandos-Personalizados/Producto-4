import socket
import os
import subprocess
import re

def exportar_configuracion_local():
    print("\n--- Exportar configuración local ---")

    try:
        resultado = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, encoding='cp850', check=True)

        with open('configuracionlocal.txt', 'w', encoding='utf-8') as archivo:
            archivo.write(resultado.stdout)

        print("\nConfiguración de red exportada a 'configuracionlocal.txt'.")

    except FileNotFoundError:
        print("\n[!] El comando 'ipconfig' no está disponible en este sistema.")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error al ejecutar el comando: {e}")
    except PermissionError:
        print("\n[!] Sin permisos para escribir en 'configuracionlocal.txt'.")
    except Exception as e:
        print(f"\n[!] Error inesperado al exportar la configuración: {str(e)}")

def seleccion_adaptador():
    print("\n--- Selección de adaptador y DNS actual ---")

    try:
        resultado = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
            capture_output=True, text=True, encoding='cp850', check=True
        )

        print("\nAdaptadores de red disponibles:\n")
        print(resultado.stdout)

        nombre_adaptador = input("Introduce el nombre del adaptador tal como aparece arriba (ej. 'Wi-Fi' o 'Ethernet'): ").strip()

        if not nombre_adaptador:
            print("\n[!] No has introducido ningún nombre de adaptador.")
            return

        print(f"\nObteniendo DNS actual del adaptador '{nombre_adaptador}'...\n")

        resultado_dns = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'dnsservers', f'name={nombre_adaptador}'],
            capture_output=True, text=True, encoding='cp850', check=True
        )

        print(resultado_dns.stdout)

    except FileNotFoundError:
        print("\n[!] El comando 'netsh' no está disponible en este sistema (es exclusivo de Windows).")
    except subprocess.CalledProcessError:
        print(f"\n[!] Error al ejecutar el comando. Revisa que el nombre del adaptador '{nombre_adaptador}' sea correcto.")
    except Exception as e:
        print(f"\n[!] Error inesperado: {str(e)}")

def resolucion_dominios():
    print("\n--- Resolución de dominios ---")
    ruta_archivo = input("Introduce la ruta del archivo de dominios (ej. web.txt): ")

    if not os.path.isfile(ruta_archivo):
        print(f"\n[!] El archivo '{ruta_archivo}' no existe o la ruta es incorrecta.")
        return

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            lineas = archivo.readlines()

            if not lineas:
                print("El archivo está vacío.")
                return

            print("\nDominios encontrados y sus IPs:")
            print("-" * 50)

            for linea in lineas:
                dominio = linea.strip()

                if not dominio:
                    continue

                print(f"Resolviendo: {dominio} ...", end=" ")

                try:
                    ip = socket.gethostbyname(dominio)
                    print(f"IP: {ip}")
                except socket.gaierror:
                    print("No se pudo resolver.")
                except Exception as e:
                    print(f"Error inesperado: {str(e)}")

    except PermissionError:
        print("\n[!] Sin permisos para leer el archivo.")
    except Exception as e:
        print(f"\n[!] Error inesperado al leer el archivo: {str(e)}")

def evaluar_y_modificar_dns():
    print("\n--- Benchmarking de DNS y modificación ---")

    nombre_adaptador = input("Introduce el nombre del adaptador a configurar (ej. 'Wi-Fi' o 'Ethernet'): ").strip()
    if not nombre_adaptador:
        print("[!] Nombre de adaptador vacío. Operación cancelada.")
        return

    dns_actual = input("Introduce la IP del DNS actual del adaptador (para comparar): ").strip()

    ips = []
    if dns_actual:
        ips.append(dns_actual)

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
        print(f"\n[!] Archivo '{ruta_dns}' no encontrado. Se usará solo el DNS actual (si se ha introducido).")

    if not ips:
        print("\n[!] No hay IPs de DNS para evaluar. Operación cancelada.")
        return

    print("\nLanzando pings a los servidores DNS...\n")
    resultados = []

    for ip in ips:
        print(f"Pinging {ip}...")
        try:
            cmd_ping = ['ping', '-n', '4', ip] if os.name == 'nt' else ['ping', '-c', '4', ip]
            res_ping = subprocess.run(cmd_ping, capture_output=True, text=True, encoding='cp850')

            tiempo_medio = float('inf')

            if res_ping.returncode == 0:
                match_win = re.search(r'(?:Media|Average) = (\d+)ms', res_ping.stdout, re.IGNORECASE)
                match_lin = re.search(r'mdev = [\d.]+/(.*?)/[\d.]+/', res_ping.stdout)

                if match_win:
                    tiempo_medio = float(match_win.group(1))
                elif match_lin:
                    try:
                        tiempo_medio = float(match_lin.group(1))
                    except ValueError:
                        pass

                if tiempo_medio == float('inf'):
                    tiempo_medio = 999.0

            resultados.append({'ip': ip, 'tiempo': tiempo_medio, 'saltos': float('inf')})
            if tiempo_medio != float('inf') and tiempo_medio != 999.0:
                print(f"Tiempo medio {ip}: {tiempo_medio} ms")
            else:
                print(f"Ping a {ip} completado (tiempo desconocido o no respondido).")

        except Exception as e:
            print(f"Error evaluando ping a {ip}: {e}")
            resultados.append({'ip': ip, 'tiempo': float('inf'), 'saltos': float('inf')})

    if not resultados:
        return

    resultados.sort(key=lambda x: x['tiempo'])
    mejor_tiempo = resultados[0]['tiempo']

    empates = [r for r in resultados if r['tiempo'] == mejor_tiempo]

    if len(empates) > 1 and mejor_tiempo != float('inf'):
        print(f"\n[i] Empate con {mejor_tiempo} ms. Lanzando tracert para desempatar...\n")
        for r in empates:
            ip = r['ip']
            print(f"Trazando ruta a {ip} (máx 15 saltos)...")
            try:
                cmd_tr = ['tracert', '-d', '-h', '15', ip] if os.name == 'nt' else ['traceroute', '-n', '-m', '15', ip]
                res_tr = subprocess.run(cmd_tr, capture_output=True, text=True, encoding='cp850')

                saltos = 0
                for linea in res_tr.stdout.split('\n'):
                    linea = linea.strip()
                    if re.match(r'^\d+', linea):
                        saltos += 1

                r['saltos'] = saltos
                print(f"Saltos hasta {ip}: {saltos}")
            except Exception as e:
                print(f"Error trazando {ip}: {e}")

        empates.sort(key=lambda x: x['saltos'])
        ganador = empates[0]
    else:
        ganador = resultados[0]

    resultados.sort(key=lambda x: (x['tiempo'], x['saltos']))

    print("\n" + "="*30)
    print("      Ranking final DNS   ")
    print("="*30)
    for i, r in enumerate(resultados):
        str_saltos = str(r['saltos']) if r['saltos'] != float('inf') else 'N/A'
        str_tiempo = f"{r['tiempo']} ms" if r['tiempo'] != float('inf') else 'Inalcanzable'
        print(f"{i+1}º - IP: {r['ip']} | Tiempo medio: {str_tiempo} | Saltos: {str_saltos}")

    ip_ganadora = ganador['ip']
    print(f"\n[+] DNS más rápido: {ip_ganadora}")

    if ip_ganadora == dns_actual:
        print("\nEl DNS actual ya es el más rápido. No se aplican cambios.")
    else:
        print(f"\n[i] Cambiando DNS del adaptador '{nombre_adaptador}' a {ip_ganadora} (requiere permisos de Administrador)...")
        if os.name == 'nt':
            try:
                comando_dns = [
                    'netsh', 'interface', 'ipv4', 'set', 'dnsservers',
                    f'name={nombre_adaptador}', 'static', ip_ganadora, 'primary'
                ]
                res_dns = subprocess.run(comando_dns, capture_output=True, text=True, encoding='cp850')

                if res_dns.returncode == 0:
                    print(f"\nDNS del adaptador '{nombre_adaptador}' cambiado a {ip_ganadora}.")
                else:
                    print("\n[!] No se pudo cambiar el DNS. Comprueba que has ejecutado el programa como Administrador.")
                    print(f"Detalle: {res_dns.stderr.strip() or res_dns.stdout.strip()}")
            except Exception as e:
                print(f"\n[!] Error ejecutando netsh: {e}")
        else:
            print("\n[!] El cambio automático con 'netsh' solo está soportado en Windows.")
