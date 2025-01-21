import requests
import time
from itertools import cycle
from threading import Thread

def load_proxies(proxy_list):
    with open(proxy_list, 'r') as file:
        proxies = file.read().splitlines()
    return cycle(proxies)

def check_stream_status(url, headers):
    try:
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error al verificar el estado de la transmisión: {e}")
        return False

def bot_view_stream(url, interval, proxy_pool, bot_id, headers):
    try:
        while True:
            if not check_stream_status(url, headers):
                print(f"La transmisión en vivo ha finalizado o no está disponible - Bot {bot_id}")
                break

            proxy = next(proxy_pool) if proxy_pool else None
            proxies = {"http": proxy, "https": proxy} if proxy else None
            session = requests.Session()
            session.headers.update(headers)

            try:
                response = session.get(url, proxies=proxies)
                print(f"Solicitando {url} - Estado: {response.status_code} - Usando Proxy: {proxy} - Bot {bot_id}:1")
            except requests.exceptions.RequestException as e:
                print(f"Error al realizar la solicitud: {e} - Usando Proxy: {proxy} - Bot {bot_id}:-1")
                time.sleep(5)

            time.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"Bot {bot_id} detenido por el usuario.")

def start_bots(url, interval, bot_count, proxy_file):
    proxy_pool = load_proxies(proxy_file) if proxy_file else None
    threads = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    for bot_id in range(1, bot_count + 1):
        thread = Thread(target=bot_view_stream, args=(url, interval, proxy_pool, bot_id, headers))
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
