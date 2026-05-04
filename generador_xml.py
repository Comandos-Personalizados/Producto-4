"""Módulo de generación del archivo XML con la información de un adaptador.

Encapsula toda la lógica de construcción del árbol XML mediante la librería
nativa xml.etree.ElementTree y el guardado en disco. La información se almacena
como contenido de elementos (text nodes) tal y como pide la rúbrica, dejando
los atributos sólo para metadatos (nombre del adaptador, número de salto, etc.).
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom


def construir_arbol(nombre_adaptador, datos, velocidad_dns_ms, saltos):
    """Construye y devuelve el árbol XML (ElementTree) con la información dada.

    Parámetros:
        nombre_adaptador: nombre del adaptador analizado.
        datos: dict con 'ip', 'mascara', 'puerta_enlace', 'dns_primario'.
        velocidad_dns_ms: float (ms) o None si no se ha podido medir.
        saltos: lista de tuplas (numero, ip) procedente de tracert.

    Estructura generada:
        <red>
            <adaptador nombre="Ethernet">
                <ip>...</ip>
                <mascara>...</mascara>
                <puerta_enlace>...</puerta_enlace>
                <dns_primario>...</dns_primario>
                <velocidad_dns unidad="ms">15</velocidad_dns>
                <trazado saltos_totales="3">
                    <salto numero="1">192.168.1.1</salto>
                    ...
                </trazado>
            </adaptador>
        </red>
    """
    raiz = ET.Element('red')
    adaptador = ET.SubElement(raiz, 'adaptador', {'nombre': nombre_adaptador or ''})

    # Datos básicos del adaptador. Si un dato falta se escribe cadena vacía
    # para mantener el XML bien formado y reflejar la ausencia del valor.
    ET.SubElement(adaptador, 'ip').text = datos.get('ip') or ''
    ET.SubElement(adaptador, 'mascara').text = datos.get('mascara') or ''
    ET.SubElement(adaptador, 'puerta_enlace').text = datos.get('puerta_enlace') or ''
    ET.SubElement(adaptador, 'dns_primario').text = datos.get('dns_primario') or ''

    # Velocidad media del DNS: la unidad la guardamos como atributo informativo.
    velocidad_el = ET.SubElement(adaptador, 'velocidad_dns', {'unidad': 'ms'})
    velocidad_el.text = '' if velocidad_dns_ms is None else str(velocidad_dns_ms)

    # Trazado: número total de saltos como atributo y cada salto como subelemento.
    trazado_el = ET.SubElement(adaptador, 'trazado', {'saltos_totales': str(len(saltos))})
    for numero, ip_salto in saltos:
        salto_el = ET.SubElement(trazado_el, 'salto', {'numero': str(numero)})
        salto_el.text = ip_salto

    return ET.ElementTree(raiz)


def guardar_xml(arbol, ruta_destino):
    """Guarda el árbol XML en la ruta indicada con sangría legible y declaración.

    Devuelve True si se ha guardado correctamente, False en caso contrario.
    Captura los errores de E/S habituales (PermissionError, OSError) para que
    el flujo principal pueda informar al usuario sin propagar la excepción.
    """
    try:
        # Convertimos a string y embellecemos con minidom para que el XML
        # sea legible al abrirlo manualmente. Es opcional para "bien formado",
        # pero ayuda a la corrección visual en la entrega.
        xml_bytes = ET.tostring(arbol.getroot(), encoding='utf-8')
        xml_bonito = minidom.parseString(xml_bytes).toprettyxml(indent='    ', encoding='utf-8')

        with open(ruta_destino, 'wb') as f:
            f.write(xml_bonito)

        return True

    except PermissionError:
        print(f"\n[!] Sin permisos para escribir en '{ruta_destino}'.")
    except OSError as e:
        print(f"\n[!] Error de E/S al guardar el XML: {e}")
    except ET.ParseError as e:
        print(f"\n[!] El XML generado no es válido: {e}")
    except Exception as e:
        print(f"\n[!] Error inesperado al guardar el XML: {e}")

    return False


def generar_xml_red(nombre_adaptador, datos, velocidad_dns_ms, saltos, ruta_destino='red.xml'):
    """Función de alto nivel: construye el árbol XML y lo persiste a disco.

    Devuelve True/False según el éxito del guardado.
    """
    arbol = construir_arbol(nombre_adaptador, datos, velocidad_dns_ms, saltos)
    return guardar_xml(arbol, ruta_destino)
