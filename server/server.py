import os
import socket
import time
import threading
import queue

class Server:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    last_client = None
    fatal_disconnect = False

    def __init__(self, host, port, Nmax=10, Nmin=5, timeout=30):
        self.host = host
        self.port = port
        self.accept_lock = threading.Lock()
        self.lock = threading.Lock()

        self.Nmax = Nmax
        self.Nmin = Nmin
        self.timeout = timeout
        self.thread_queue = queue.Queue()

        threading.Thread(target=self.create_thread).start()

    def create_thread(self):
        while True:
            self.thread_queue.get()
            if threading.active_count() < self.Nmax:
                self.accept_client()


    def start_server(self):
        while True:
            self.thread_queue.put(None)


    def accept_client(self):
        with self.accept_lock:
            client_socket, client_address = self.server_socket.accept()
            print(f"Принято подключение от {client_address}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address, self.lock))
            client_thread.start()

    def handle_client(self, client_socket:socket.socket, client_address, lock: threading.Lock):
        try:
            while True:
                client_socket.settimeout(self.timeout)
                time.sleep(0.05)
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                if data == "ECHO":
                    self.get_msg(client_socket)

                elif data == "TIME":
                    lock.acquire()
                    print("Пришёл запрос на получение времени")
                    lock.release()
                    self.send_time(client_socket)

                elif data == "UPLOAD":
                    self.upload_to_server(client_socket, client_address)

                elif data == "DOWNLOAD":
                    file_name = self.receive(client_socket)
                    if os.path.exists(file_name):
                        self.download_from_server(file_name, client_socket, client_address)
                    else:
                        self.send("Файл не найден", client_socket)

                elif data == "CLOSE":
                    self.close_connection(client_socket)
                    break

                else:
                    response = "Неверная команда. Поддерживаемые команды: ECHO, TIME, CLOSE, UPLOAD, DOWNLOAD"
                    self.send(response, client_socket)
        except socket.timeout:
            self.close_connection(client_socket)
            exit(1)

    def create_server_connection(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(100)
        print(f"Сервер слушает на {self.host}:{self.port}")

    def send(self, msg: str, client_socket):
        client_socket.send(msg.encode())

    def send_bytes(self, msg: bytes, client_socket):
        client_socket.send(msg)

    def receive_oob(self, client_socket):
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 1)
        data = self.receive_bytes(client_socket)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 0)
        return data

    def receive(self, client_socket, size: int = 1024) -> str:
        return client_socket.recv(size).decode()

    def receive_bytes(self, client_socket, size: int = 1024) -> bytes:
        return client_socket.recv(size)


    def get_msg(self, client_socket):
        echo_data = self.receive(client_socket)
        print(f"Клиент отправил сообщение {echo_data}")
        self.send(f"Вы сказали: {echo_data}", client_socket)

    def send_time(self, client_socket):
        current_time = time.ctime(time.time())
        self.send(current_time, client_socket)

    def upload_to_server(self, client_socket, client_address):
        file_name = self.receive(client_socket)
        file_size = int(self.receive(client_socket))
        if (self.last_client is not None
                and self.last_client[0] == client_address
                and self.fatal_disconnect is True):
            self.fatal_disconnect = False
            if os.path.exists(file_name):
                exist_file_size = os.path.getsize(file_name)
                self.send(str(exist_file_size), client_socket)
                file = open(file_name, 'ab')
                file.seek(exist_file_size)
                file_size -= exist_file_size
            else:
                self.send(str(0), client_socket)
                file = open(file_name, 'wb')
        else:
            self.fatal_disconnect = False
            self.last_client = client_address
            self.send(str(0), client_socket)
            file = open(file_name, 'wb')
        bytes_received = 0
        try:
            print("Закачка файла на сервер")
            oob_data = file_size / 4
            print(f"Количество срочных данных: {oob_data}")
            start_time = time.time()
            while bytes_received < file_size:
                if oob_data > bytes_received:
                    data = self.receive_oob(client_socket)
                else:
                    data = self.receive_bytes(client_socket)
                if not data:
                    self.fatal_disconnect = True
                    break
                file.write(data)
                bytes_received += len(data)
            else:
                end_time = time.time()
                elapsed_time = end_time - start_time
                bitrate = (file_size * 8) / (elapsed_time * 1024 * 1024)
                print(f"Файл '{file_name}' загружен на сервер. Было принято {oob_data} срочнных данных")
                self.send(f"Битрейт: {bitrate:.2f} Mbps", client_socket)

        except socket.error as e:
            print(f"Произошла ошибка: {str(e)}")
            self.fatal_disconnect = True
        finally:
            file.close()

    def download_from_server(self, file_name, client_socket, client_address):
        if (self.last_client is not None
                and self.last_client[0] == client_address
                and self.fatal_disconnect is True):
            self.fatal_disconnect = False
            self.send("Докачка файла", client_socket)
            self.send(str(os.path.getsize(file_name)), client_socket)
            file = open(file_name, 'rb')
            file_offset = int(self.receive(client_socket))
            file.seek(file_offset)
        else:
            self.fatal_disconnect = False
            self.last_client = client_address
            self.send(str(os.path.getsize(file_name)), client_socket)
            file = open(file_name, 'rb')
        try:
            print(f"Пришёл запрос на отправку файла {file_name}")
            for data in iter(lambda: file.read(1024), b''):
                self.send_bytes(data, client_socket)
            print(f"Файл '{file_name}' отправлен клиенту")
        except Exception:
            print("Клиент отключился")
            self.fatal_disconnect = True
        finally:
            file.close()

    def close_connection(self, client_socket):
        self.send("Соединение закрыто.", client_socket)
        client_socket.close()

    def close_server(self):
        self.server_socket.close()
