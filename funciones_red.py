"""Librería de funciones de red usada por main.py.

Contiene la lógica del Producto 3 (resolución de dominios, exportación de
configuración, selección de adaptador, benchmarking de DNS) más las funciones
nuevas del Producto 4 (extracción de datos del adaptador, ping, tracert y
flujo orquestador que delega la escritura del XML en generador_xml).
"""

import socket
import os
import subprocess
import re

import generador_xml


def generar_xml_adaptador():
    """Flujo principal del Producto 4: pide un adaptador, recoge sus datos y crea el XML.

    Pasos:
        1. Lista los adaptadores disponibles vía netsh.
        2. Pide al usuario que escoja uno (por número o por nombre exacto).
        3. Extrae IP, máscara, puerta de enlace y DNS primario con ipconfig /all.
        4. Mide la velocidad media de respuesta del DNS con ping.
        5. Lanza tracert al DNS y guarda el número de saltos y la IP de cada uno.
        6. Llama al módulo generador_xml para escribir el archivo XML resultante.
    """
    print("\n--- Generación del archivo XML de red ---")

    adaptadores = listar_adaptadores()
    if not adaptadores:
        print("\n[!] No se han podido detectar adaptadores. Introduce el nombre manualmente.")
    else:
        print("\nAdaptadores detectados:")
        for i, nombre in enumerate(adaptadores, start=1):
            print(f"  {i}. {nombre}")

    seleccion = input("\nIntroduce el número del adaptador o su nombre exacto: ").strip()
    if not seleccion:
        print("\n[!] No has introducido ningún valor. Operación cancelada.")
        return

    # Permitimos seleccionar por índice (más cómodo) o escribiendo el nombre.
    if seleccion.isdigit() and adaptadores:
        idx = int(seleccion)
        if 1 <= idx <= len(adaptadores):
            nombre_adaptador = adaptadores[idx - 1]
        else:
            print("\n[!] Índice fuera de rango. Operación cancelada.")
            return
    else:
        nombre_adaptador = seleccion

    print(f"\n[i] Adaptador seleccionado: {nombre_adaptador}")

    print("[i] Extrayendo IP, máscara, puerta de enlace y DNS primario...")
    datos = obtener_datos_adaptador(nombre_adaptador)

    if not datos.get('ip'):
        print("\n[!] No se ha podido extraer la IP del adaptador. ¿Está conectado y el nombre es correcto?")
        # Aun así seguimos con lo que tengamos para que el XML refleje el estado real.

    print(f"  IP:             {datos.get('ip') or 'N/D'}")
    print(f"  Máscara:        {datos.get('mascara') or 'N/D'}")
    print(f"  Puerta enlace:  {datos.get('puerta_enlace') or 'N/D'}")
    print(f"  DNS primario:   {datos.get('dns_primario') or 'N/D'}")

    velocidad = None
    saltos = []
    ip_dns = datos.get('dns_primario')

    if ip_dns:
        print(f"\n[i] Midiendo velocidad media de ping a {ip_dns}...")
        velocidad = obtener_velocidad_dns(ip_dns)
        if velocidad is not None:
            print(f"  Velocidad media: {velocidad} ms")
        else:
            print("  [!] No se pudo medir la velocidad media (sin respuesta).")

        print(f"\n[i] Trazando ruta hasta {ip_dns} (esto puede tardar)...")
        saltos = obtener_trazado(ip_dns)
        if saltos:
            print(f"  Saltos totales: {len(saltos)}")
            for numero, ip_salto in saltos:
                print(f"    {numero:>2}. {ip_salto}")
        else:
            print("  [!] No se ha obtenido ningún salto del tracert.")
    else:
        print("\n[!] Sin DNS primario; se omiten ping y tracert.")

    ruta_destino = input("\nNombre del archivo XML a generar (ENTER para 'red.xml'): ").strip() or 'red.xml'

    if generador_xml.generar_xml_red(nombre_adaptador, datos, velocidad, saltos, ruta_destino):
        print(f"\n[+] Archivo XML generado correctamente: '{ruta_destino}'")
    else:
        print("\n[!] No se ha podido generar el archivo XML.")


def listar_adaptadores():
    """Devuelve una lista con los nombres de los adaptadores de red activos.

    Lanza 'netsh interface ipv4 show interfaces' y parsea la última columna
    de cada fila de datos (que contiene el nombre del adaptador).
    Retorna una lista de strings; vacía si el comando falla.
    """
    nombres = []
    try:
        resultado = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
            capture_output=True, text=True, encoding='cp850', check=True
        )

        # Las líneas útiles empiezan con espacios y una columna numérica (Idx).
        # Formato: Idx  Mét  MTU   Estado          Nombre
        for linea in resultado.stdout.splitlines():
            partes = linea.split()
            if len(partes) >= 5 and partes[0].isdigit():
                # El nombre del adaptador puede contener espacios -> unimos a partir del índice 4
                nombre = ' '.join(partes[4:])
                nombres.append(nombre)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    except Exception:
        pass

    return nombres


def obtener_datos_adaptador(nombre_adaptador):
    """Extrae IP, máscara, puerta de enlace y DNS primario del adaptador indicado.

    Ejecuta 'ipconfig /all', localiza la sección del adaptador buscado y aplica
    expresiones regulares para extraer los campos relevantes. Devuelve un dict:
        {'ip': ..., 'mascara': ..., 'puerta_enlace': ..., 'dns_primario': ...}
    Cada campo será una cadena o None si no se encuentra.
    """
    datos = {'ip': None, 'mascara': None, 'puerta_enlace': None, 'dns_primario': None}

    try:
        resultado = subprocess.run(
            ['ipconfig', '/all'],
            capture_output=True, text=True, encoding='cp850', check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return datos

    salida = resultado.stdout

    # Localizamos el bloque del adaptador. ipconfig agrupa por "Adaptador X NombreAdaptador:".
    # Dividimos por dobles saltos de línea para tratar cada bloque independientemente.
    bloques = re.split(r'\r?\n\r?\n', salida)
    bloque_adaptador = None
    nombre_norm = nombre_adaptador.strip().lower()

    for bloque in bloques:
        cabecera = bloque.splitlines()[0] if bloque.strip() else ''
        # Buscamos el bloque cuya primera línea contenga el nombre del adaptador.
        if nombre_norm and nombre_norm in cabecera.lower():
            bloque_adaptador = bloque
            break

    if bloque_adaptador is None:
        return datos

    # Patrones tolerantes a la variación de etiquetas en español/inglés de Windows.
    patron_ip = re.compile(r'(?:Direcci[oó]n IPv4|IPv4 Address)[\.\s]*:\s*([\d\.]+)', re.IGNORECASE)
    patron_mascara = re.compile(r'(?:M[aá]scara de subred|Subnet Mask)[\.\s]*:\s*([\d\.]+)', re.IGNORECASE)
    patron_gateway = re.compile(r'(?:Puerta de enlace predeterminada|Default Gateway)[\.\s]*:\s*([\d\.]+)', re.IGNORECASE)
    patron_dns = re.compile(r'(?:Servidores DNS|DNS Servers)[\.\s]*:\s*([\d\.]+)', re.IGNORECASE)

    m = patron_ip.search(bloque_adaptador)
    if m:
        datos['ip'] = m.group(1)

    m = patron_mascara.search(bloque_adaptador)
    if m:
        datos['mascara'] = m.group(1)

    m = patron_gateway.search(bloque_adaptador)
    if m:
        datos['puerta_enlace'] = m.group(1)

    m = patron_dns.search(bloque_adaptador)
    if m:
        datos['dns_primario'] = m.group(1)

    return datos


def obtener_velocidad_dns(ip_dns, intentos=4):
    """Lanza un ping al DNS y devuelve el tiempo medio en ms (float) o None si falla."""
    if not ip_dns:
        return None

    try:
        cmd = ['ping', '-n', str(intentos), ip_dns] if os.name == 'nt' else ['ping', '-c', str(intentos), ip_dns]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='cp850')

        if res.returncode != 0:
            return None

        # Windows (es): "Media = 15ms" / Windows (en): "Average = 15ms"
        m_win = re.search(r'(?:Media|Average)\s*=\s*(\d+)\s*ms', res.stdout, re.IGNORECASE)
        if m_win:
            return float(m_win.group(1))

        # Linux: "rtt min/avg/max/mdev = 0.123/0.456/0.789/0.012 ms"
        m_lin = re.search(r'=\s*[\d.]+/([\d.]+)/[\d.]+/', res.stdout)
        if m_lin:
            return float(m_lin.group(1))

    except Exception:
        return None

    return None


def obtener_trazado(ip_dns, max_saltos=30):
    """Ejecuta tracert hasta la IP del DNS y devuelve la lista de IPs por salto.

    Devuelve una lista de tuplas (numero_salto, ip_salto). Si en un salto no se
    obtiene IP (timeout, '*'), se devuelve la cadena '*' como ip de ese salto.
    """
    saltos = []
    if not ip_dns:
        return saltos

    try:
        if os.name == 'nt':
            cmd = ['tracert', '-d', '-h', str(max_saltos), ip_dns]
        else:
            cmd = ['traceroute', '-n', '-m', str(max_saltos), ip_dns]

        res = subprocess.run(cmd, capture_output=True, text=True, encoding='cp850')
    except FileNotFoundError:
        return saltos
    except Exception:
        return saltos

    # Cada línea válida empieza con el número de salto. Extraemos la primera IP que aparezca.
    patron_ip = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b')
    for linea in res.stdout.splitlines():
        linea_strip = linea.strip()
        m_num = re.match(r'^(\d+)\s', linea_strip)
        if not m_num:
            continue

        numero = int(m_num.group(1))
        m_ip = patron_ip.search(linea_strip)
        ip_salto = m_ip.group(1) if m_ip else '*'
        saltos.append((numero, ip_salto))

    return saltos


def exportar_configuracion_local():
    """Vuelca la salida de 'ipconfig /all' a 'configuracionlocal.txt'."""
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
    """Muestra los adaptadores disponibles y los DNS configurados en el elegido."""
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
    """Lee un fichero de dominios y muestra la IP asociada a cada uno."""
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
    """Hace ping a una lista de DNS, los ordena por velocidad y aplica el ganador."""
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
