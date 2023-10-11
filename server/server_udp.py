import os
import socket
import time
import random


class ServerUDP:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    last_client = None
    fatal_disconnect = False

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def create_server_connection(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(100)
        print(f"Сервер UDP слушает на {self.host}:{self.port}")

    def send(self, message: str, address):
        self.server_socket.sendto(message.encode(), address)

    def recv(self, size = 2048):
        response = self.server_socket.recvfrom(size)
        return response

    def send_time(self, address):
        current_time = time.ctime(time.time())
        self.send(current_time, address)

    def close_server(self):
        self.server_socket.close()

    def upload_file(self, file_name, lines, address):
        data_file = {}
        while True:

            data, _ = self.recv()
            received_sequence_number, message = data.decode().split(":")
            received_sequence_number = int(received_sequence_number)

            if message == "END_OF_FILE":
                while True:
                    if len(data_file) != lines:
                        self.send("Err", address)
                        full_set = set(range(1, lines))
                        existing_set = set(list(data_file))
                        missing_numbers = full_set.difference(existing_set)
                        missing_numbers_list = list(missing_numbers)
                        for num in missing_numbers_list:
                            self.send(f"{num}", address)
                            data, _ = self.recv()
                            received_sequence_number, message = data.decode().split(":")
                            received_sequence_number = int(received_sequence_number)
                            data_file[received_sequence_number] = message
                    else:
                        break
                self.send("END", address)
                break

            if random.randint(1, 100) < 5:
                continue
            data_file[received_sequence_number] = message
            acknowledgment = f"Acknowledgment for sequence number {received_sequence_number}"
            self.send(acknowledgment, address)

        with open(file_name, 'wb') as file:
            data_file = dict(sorted(data_file.items()))
            res = ""
            for v in data_file.values():
                res += v
            file.write(bytes.fromhex(res))
        print("Файл загружен.")

    def download_file(self, file_name, address):
        if not os.path.exists(file_name):
            print("Файл не найден")
            return
        self.send("UPLOAD", address)
        window_size = 3
        sequence_number = 0
        all_blocks_sent = False
        with open(file_name, 'rb') as file:
            messages = file.read()
        messages = messages.hex()
        self.send(str(len(messages)), address)
        while not all_blocks_sent:

            try:
                for i in range(window_size):
                    message = f"{sequence_number}:{messages[sequence_number]}"
                    self.send(message, address)
                    sequence_number += 1
            except IndexError:
                all_blocks_sent = True
                self.send(f"{sequence_number}:END_OF_FILE", address)

            try:
                self.server_socket.settimeout(5)
                for i in range(window_size - 1):
                    acknowledgment = self.recv()[0].decode()
                    if all_blocks_sent:
                        while acknowledgment != "END":
                            acknowledgment = self.recv()[0].decode()
                            if acknowledgment.split()[0] == "Err":
                                while acknowledgment != "END":
                                    number = self.recv()[0].decode().split()[0]
                                    if number == "END":
                                        break
                                    elif number == "Err":
                                        continue
                                    self.send(f"{number}:{messages[int(number)]}", address)
                                break
                            print(acknowledgment)
                        break
                    print(acknowledgment)
                self.server_socket.settimeout(None)

                if window_size < 10:
                    window_size += 1

            except socket.timeout:
                print("Таймаут при ожидании подтверждения.")
                window_size = max(window_size // 2, 1)

            if all_blocks_sent:
                print("Файл успешно отправлен")
                break