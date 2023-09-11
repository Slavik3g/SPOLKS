import os
import socket

from utils.progress_bar import progress


class Client:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, address, port):
        self.server_host = address
        self.server_port = port

    def send(self, msg: str):
        self.client_socket.send(msg.encode())

    def send_bytes(self, msg: bytes):
        self.client_socket.send(msg)

    def send_oob(self, data: bytes):
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 1)
        self.send_bytes(data)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 0)

    def receive(self, size: int = 1024) -> str:
        return self.client_socket.recv(size).decode()

    def receive_bytes(self, size: int = 1024) -> bytes:
        return self.client_socket.recv(size)

    def create_connection(self):
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"Подключено к серверу {self.server_host}:{self.server_port}")
        except:
            print("Ошибка подключения")
            exit(1)

    def close_connection(self):
        self.client_socket.close()
        print("Соединение с сервером закрыто")

    def download_from_server(self, file_name):
        self.send(file_name)
        response = self.receive()
        if response == "Файл не найден":
            print("Файл не найден на сервере")
        else:
            if response == "Докачка файла":
                print(f"Будет произведена докачка файла с сервера")
                file_size = int(self.receive())
                curr_file_size = os.path.getsize(file_name)
                self.send(str(curr_file_size))
                file_size -= curr_file_size
                file = open(file_name, "ab")
            else:
                file_size = int(response)
                file = open(file_name, "wb")

            bytes_received = 0
            try:
                while bytes_received < file_size:
                    progress(bytes_received, file_size)
                    data = self.receive_bytes()
                    file.write(data)
                    bytes_received += len(data)
                print(f"\nФайл '{file_name}' скачан с сервера")
            finally:
                file.close()

    def upload_to_server(self, file_name: str):
        self.send(file_name)
        file_size = os.path.getsize(file_name)
        self.send(str(file_size))
        sent_size = int(self.receive())
        with open(file_name, 'rb') as file:
            file.seek(sent_size)
            oob_data = (file_size - sent_size) / 4
            print(f"Количество срочных данных: {oob_data}")
            for data in iter(lambda: file.read(1024), b''):
                progress(sent_size, file_size)
                if oob_data > sent_size:
                    self.send_oob(data)
                    print(f"Отправленно {sent_size} срочных данных", end='')
                else:
                    self.send_bytes(data)
                sent_size += len(data)
        print(f"\nФайл '{file_name}' загружен на сервер")
        bitrate = self.receive()
        print(bitrate)

    def send_message(self, msg):
        self.send(msg)
        response = self.receive()
        return response

    def get_time(self):
        return self.receive()
