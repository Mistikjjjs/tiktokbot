import os
import uuid
import shutil
import time
import random
import datetime
import requests
from threading import Thread, Semaphore
from streamlink import Streamlink
from fake_useragent import UserAgent
from requests import RequestException
import streamlink

class ViewerBot:
    def __init__(self, nb_of_threads, channel_name, proxylist, proxy_imported, timeout, stop=False, type_of_proxy="http"):
        self.nb_of_threads = nb_of_threads
        self.nb_requests = 0
        self.stop_event = stop
        self.proxylist = proxylist
        self.all_proxies = []
        self.proxyrefreshed = True
        self.debug_mode = False
        self.current_url = None
        self.url_refresh_thread = Thread(target=self.refresh_url)
        self.url_refresh_thread.start()

        self.type_of_proxy = type_of_proxy if isinstance(type_of_proxy, str) else type_of_proxy.get()
        self.proxy_imported = proxy_imported
        self.timeout = timeout
        self.channel_url = f"https://www.kick.com/{channel_name.lower()}"
        self.proxyreturned1time = False
        self.thread_semaphore = Semaphore(int(nb_of_threads))  # Semaphore to control thread count
        self.session = self.create_session()
        self.ensure_plugin_installed()

    def create_session(self):
        # Create a session for making requests
        self.ua = UserAgent()
        session = Streamlink()
        if 'kick' not in session.get_plugins():
            print("The Kick plugin is not installed, please install it and try again.")
            return
        session.set_option("http-headers", {
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.ua.random,
            "Client-ID": "ewvlchtxgqq88ru9gmfp1gmyt6h2b93",
            "Referer": "https://www.google.com/",
        })
        return session

    def ensure_plugin_installed(self):
        plugins_dir = streamlink.plugins.__path__[0]
        plugin_file = os.path.join(plugins_dir, "kick.py")
        plugin_source = os.path.dirname(os.path.abspath(__file__)) + "/streamlinks_plugins/kick.py"
        
        if not os.path.exists(plugin_file):
            shutil.copy(plugin_source, plugins_dir)
            print("The Kick plugin has been added successfully.")
        else:
            shutil.copy(plugin_source, plugins_dir)
            print("The Kick plugin has been updated successfully.")

    def make_request_with_retry(self, session, url, proxy, headers, proxy_used, max_retries=3):
        backoff_time = 1  # Initial backoff time in seconds
        for _ in range(max_retries):
            try:
                # Send requests to the Kick service
                response = session.get(url, proxies=proxy, headers=headers, timeout=(self.timeout / 1000) + 1)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # HTTP status code for "Too Many Requests"
                    print(f"Rate limit reached. Waiting for {backoff_time} seconds.")
                    time.sleep(backoff_time)
                    backoff_time *= 2  # Double the backoff time
                else:
                    if proxy_used in self.proxies:
                        self.proxies.remove(proxy_used)
                    return None
            except RequestException as e:
                if "400 Bad Request" in str(e) or "403 Forbidden" in str(e) or "RemoteDisconnected" in str(e) or "connect timeout=10.0" in str(e):
                    if proxy_used in self.proxies:
                        self.proxies.remove(proxy_used)
                continue
        return None

    def get_proxies(self):
        if not self.proxylist or not self.proxyrefreshed:
            try:
                response = requests.get(
                    f"https://api.proxyscrape.com/v2/?request=displayproxies&protocol={self.type_of_proxy}&timeout={self.timeout}&country=all&ssl=all&anonymity=all"
                )
                if response.status_code == 200:
                    lines = [line.strip() for line in response.text.split("\n") if line.strip()]
                    self.proxyrefreshed = True
                    return lines
            except Exception as e:
                print(f"Error fetching proxies: {e}")
                pass
        elif not self.proxyreturned1time:
            self.proxyreturned1time = True
            return self.proxylist
        return []

    def get_url(self, session, max_retries=10):
        backoff_time = 0.1  # Initial backoff time in seconds
        for _ in range(max_retries):
            try:
                streams = session.streams(self.channel_url)
                if streams:
                    return streams.get('worst', streams.get('best')).url
                else:
                    if self.debug_mode:
                        print(f"No suitable stream found for URL: {self.channel_url}")
                    print(f"No streams found. Waiting for {backoff_time} seconds.")
                    time.sleep(backoff_time)
                    backoff_time *= 2  # Double the backoff time
            except streamlink.exceptions.NoPluginError:
                if self.debug_mode:
                    print(f"No plugin to handle URL: {self.channel_url}")
            except streamlink.exceptions.PluginError as e:
                if self.debug_mode:
                    print(f"Plugin error: {str(e)}")
            except Exception as e:
                if self.debug_mode:
                    print(f"Error getting URL: {e}")
        return None

    def open_url(self, proxy_data):
        headers = {
            'User-Agent': self.ua.random, 
            'Client-ID': 'ewvlchtxgqq88ru9gmfp1gmyt6h2b93',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        current_proxy = self.build_proxy(proxy_data)
        try:
            response = self.make_request_with_retry(requests.Session(), self.current_url, current_proxy, headers, proxy_data['proxy'])
            if response:
                self.nb_requests += 1
                proxy_data['time'] = time.time()
            self.all_proxies[self.all_proxies.index(proxy_data)] = proxy_data
        except Exception as e:
            print(f"Error opening URL with proxy: {e}")
        finally:
            self.thread_semaphore.release()

    def build_proxy(self, proxy_data):
        username, password = proxy_data.get('username'), proxy_data.get('password')
        proxy = proxy_data['proxy']
        if username and password:
            return {"http": f"{username}:{password}@{proxy}", "https": f"{username}:{password}@{proxy}"}
        return {"http": proxy, "https": proxy}

    def stop(self):
        self.stop_event = True
        print("Stopping the ViewerBot.")

    def refresh_url(self):
        while not self.stop_event:
            session = self.create_session()
            self.current_url = self.get_url(session)
            time.sleep(1)

    def main(self):
        self.proxies = self.get_proxies()
        start_time = datetime.datetime.now()

        while not self.stop_event:
            elapsed_seconds = (datetime.datetime.now() - start_time).total_seconds()
            self.all_proxies = [{'proxy': p, 'time': time.time()} for p in self.proxies]

            for proxy_data in self.all_proxies:
                self.thread_semaphore.acquire()
                thread = Thread(target=self.open_url, args=(proxy_data,))
                thread.daemon = True
                thread.start()

            if elapsed_seconds >= 300 and not self.proxy_imported:
                start_time = datetime.datetime.now()
                self.proxies = self.get_proxies()
                self.proxyrefreshed = False

            if self.stop_event:
                break
