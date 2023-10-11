import os
import random
import socket
from pprint import pprint


class ClientUDP:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __init__(self, address, port):
        self.server_host = address
        self.server_port = port

    def close_client(self):
        self.client_socket.close()

    def send(self, message:str):
        self.client_socket.sendto(message.encode(), (self.server_host, self.server_port))

    def recv(self, size = 2048):
        response = self.client_socket.recvfrom(size)
        return response

    def get_time(self):
        self.send("time")
        response = self.recv()
        return response[0].decode()

    def download_file(self, file_name, lines):
        data_file = {}
        while True:

            data, _ = self.recv()
            received_sequence_number, message = data.decode().split(":")
            received_sequence_number = int(received_sequence_number)

            if message == "END_OF_FILE":
                while True:
                    if len(data_file) != lines:
                        self.send("Err")
                        full_set = set(range(1, lines))
                        existing_set = set(list(data_file))
                        missing_numbers = full_set.difference(existing_set)
                        missing_numbers_list = list(missing_numbers)
                        for num in missing_numbers_list:
                            self.send(f"{num}")
                            data, _ = self.recv()
                            received_sequence_number, message = data.decode().split(":")
                            received_sequence_number = int(received_sequence_number)
                            data_file[received_sequence_number] = message
                    else:
                        break
                self.send("END")
                break

            if random.randint(1, 100) < 5:
                continue
            data_file[received_sequence_number] = message
            acknowledgment = f"Acknowledgment for sequence number {received_sequence_number}"
            self.send(acknowledgment)

        with open(file_name, 'wb') as file:
            data_file = dict(sorted(data_file.items()))
            res = ""
            for v in data_file.values():
                res += v
            file.write(bytes.fromhex(res))
        print("Файл скачан.")

    def upload_file(self, file_name):
        if not os.path.exists(file_name):
            print("Файл не найден")
            return
        self.send("UPLOAD")
        self.send(file_name)
        window_size = 3
        sequence_number = 0
        all_blocks_sent = False
        with open(file_name, 'rb') as file:
            messages = file.read()
        messages = messages.hex()
        self.send(str(len(messages)))
        while not all_blocks_sent:

            try:
                for i in range(window_size):
                    message = f"{sequence_number}:{messages[sequence_number]}"
                    self.send(message)
                    sequence_number += 1
            except IndexError:
                all_blocks_sent = True
                self.send(f"{sequence_number}:END_OF_FILE")

            try:
                self.client_socket.settimeout(5)
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
                                    self.send(f"{number}:{messages[int(number)]}")
                                break
                            print(acknowledgment)
                        break
                    print(acknowledgment)
                self.client_socket.settimeout(None)

                if window_size < 10:
                    window_size += 1

            except socket.timeout:
                print("Таймаут при ожидании подтверждения.")
                window_size = max(window_size // 2, 1)

            if all_blocks_sent:
                print("Файл успешно отправлен")
                break