import requests
import time
from itertools import cycle
from threading import Thread

def load_proxies(proxy_list):
    """
    Carga una lista de proxies desde un archivo de texto.
    
    :param proxy_list: Nombre del archivo que contiene los proxies.
    :return: Un iterador cíclico de proxies.
    """
    with open(proxy_list, 'r') as file:
        proxies = file.read().splitlines()
    return cycle(proxies)

def check_stream_status(url):
    """
    Verifica si la transmisión en vivo sigue activa.
    
    :param url: La URL de la transmisión en vivo.
    :return: True si la transmisión está activa, False en caso contrario.
    """
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error al verificar el estado de la transmisión: {e}")
        return False

def bot_view_stream(url, interval, proxy_pool, bot_id):
    """
    Función para que un bot simule vistas a una transmisión en vivo.
    
    :param url: La URL de la transmisión en vivo.
    :param interval: El intervalo de tiempo (en segundos) entre cada solicitud.
    :param proxy_pool: Iterador cíclico de proxies.
    :param bot_id: Identificador del bot.
    """
    try:
        while True:
            # Verificar el estado de la transmisión
            if not check_stream_status(url):
                print(f"La transmisión en vivo ha finalizado o no está disponible - Bot {bot_id}")
                break

            # Seleccionar un proxy si está disponible
            proxy = next(proxy_pool) if proxy_pool else None
            proxies = {"http": proxy, "https": proxy} if proxy else None
            
            # Realizar la solicitud HTTP
            try:
                response = requests.get(url, proxies=proxies)
                print(f"Solicitando {url} - Estado: {response.status_code} - Usando Proxy: {proxy} - Bot {bot_id}:1")
            except requests.exceptions.RequestException as e:
                print(f"Error al realizar la solicitud: {e} - Usando Proxy: {proxy} - Bot {bot_id}:-1")
                time.sleep(5)  # Espera 5 segundos antes de intentar con el siguiente proxy

            # Esperar el intervalo especificado
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"Bot {bot_id} detenido por el usuario.")

def start_bots(url, interval, bot_count, proxy_file):
    """
    Inicia múltiples bots para simular vistas a una transmisión en vivo.
    
    :param url: La URL de la transmisión en vivo.
    :param interval: El intervalo de tiempo (en segundos) entre cada solicitud.
    :param bot_count: Número de bots a utilizar.
    :param proxy_file: Archivo que contiene una lista de proxies.
    """
    proxy_pool = load_proxies(proxy_file) if proxy_file else None
    threads = []

    for bot_id in range(1, bot_count + 1):
        thread = Thread(target=bot_view_stream, args=(url, interval, proxy_pool, bot_id))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

# Solicitar al usuario el enlace del live y la cantidad de bots
stream_url = input("Por favor, ingresa el enlace de tu live: ")
bot_count = int(input("Por favor, ingresa la cantidad de bots: "))
proxy_file = "proxies.txt"  # Archivo que contiene una lista de proxies

# Ejecutar los bots
start_bots(stream_url, interval=10, bot_count=bot_count, proxy_file=proxy_file)
