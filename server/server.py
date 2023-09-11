import os
import socket
import time


class Server:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    last_client = None
    fatal_disconnect = False

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_address = None
        self.client_socket = None

    def create_server_connection(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(100)
        print(f"Сервер слушает на {self.host}:{self.port}")

    def accept_client(self):
        self.client_socket, self.client_address = self.server_socket.accept()
        print(f"Подключен клиент с адресом {self.client_address}")

    def send(self, msg: str):
        self.client_socket.send(msg.encode())

    def send_bytes(self, msg: bytes):
        self.client_socket.send(msg)

    def receive_oob(self):
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 1)
        data = self.receive_bytes()
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 0)
        return data

    def receive(self, size: int = 1024) -> str:
        return self.client_socket.recv(size).decode()

    def receive_bytes(self, size: int = 1024) -> bytes:
        return self.client_socket.recv(size)


    def get_msg(self):
        echo_data = self.receive()
        print(f"Клиент отправил сообщение {echo_data}")
        self.send(f"Вы сказали: {echo_data}")

    def send_time(self):
        current_time = time.ctime(time.time())
        self.send(current_time)

    def upload_to_server(self):
        file_name = self.receive()
        file_size = int(self.receive())
        if (self.last_client is not None
                and self.last_client[0] == self.client_address[0]
                and self.fatal_disconnect is True):
            self.fatal_disconnect = False
            if os.path.exists(file_name):
                exist_file_size = os.path.getsize(file_name)
                self.send(str(exist_file_size))
                file = open(file_name, 'ab')
                file.seek(exist_file_size)
                file_size -= exist_file_size
            else:
                self.send(str(0))
                file = open(file_name, 'wb')
        else:
            self.fatal_disconnect = False
            self.last_client = self.client_address
            self.send(str(0))
            file = open(file_name, 'wb')
        bytes_received = 0
        try:
            print("Закачка файла на сервер")
            oob_data = file_size / 4
            print(f"Количество срочных данных: {oob_data}")
            start_time = time.time()
            while bytes_received < file_size:
                if oob_data > bytes_received:
                    data = self.receive_oob()
                else:
                    data = self.receive_bytes()
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
                self.send(f"Битрейт: {bitrate:.2f} Mbps")

        except socket.error as e:
            print(f"Произошла ошибка: {str(e)}")
            self.fatal_disconnect = True
        finally:
            file.close()

    def download_from_server(self, file_name):
        if (self.last_client is not None
                and self.last_client[0] == self.client_address[0]
                and self.fatal_disconnect is True):
            self.fatal_disconnect = False
            self.send("Докачка файла")
            self.send(str(os.path.getsize(file_name)))
            file = open(file_name, 'rb')
            file_offset = int(self.receive())
            file.seek(file_offset)
        else:
            self.fatal_disconnect = False
            self.last_client = self.client_address
            self.send(str(os.path.getsize(file_name)))
            file = open(file_name, 'rb')
        try:
            print(f"Пришёл запрос на отправку файла {file_name}")
            for data in iter(lambda: file.read(1024), b''):
                self.send_bytes(data)
            print(f"Файл '{file_name}' отправлен клиенту")
        except Exception:
            print("Клиент отключился")
            self.fatal_disconnect = True
        finally:
            file.close()

    def close_connection(self):
        self.send("Соединение закрыто.")
        self.client_socket.close()

    def close_server(self):
        self.server_socket.close()
