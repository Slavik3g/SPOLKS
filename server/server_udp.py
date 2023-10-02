import os
import socket
import time


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

    def recv(self, size = 512):
        response = self.server_socket.recvfrom(size)
        return response

    def send_time(self, address):
        current_time = time.ctime(time.time())
        self.send(current_time, address)

    def close_server(self):
        self.server_socket.close()

    def upload_file(self):
        expected_sequence_number = 0
        file_data = ""
        fake_timeout = True
        file_name, client_address = self.recv()
        while True:
            data, client_address = self.recv()
            received_sequence_number, message = data.decode().split(":")
            received_sequence_number = int(received_sequence_number)

            if message == "END_OF_FILE":
                print("Получен маркер конца файла.")
                acknowledgment = f"Acknowledgment for sequence number {received_sequence_number}"
                self.send(acknowledgment, client_address)
                self.send("END", client_address)
                break

            if received_sequence_number == expected_sequence_number:
                file_data += message
                if fake_timeout:
                    fake_timeout = False
                    # time.sleep(6)
                acknowledgment = f"Acknowledgment for sequence number {received_sequence_number}"
                self.send(acknowledgment, client_address)

                expected_sequence_number += 1
            else:
                print("Пропущено сообщение с номером последовательности", received_sequence_number)

        with open(file_name.decode(), 'w') as file:
            file.write(file_data)

    def download_file(self, file_path, address):
        if not os.path.exists(file_path):
            print(f"Файл {file_path} не найден")
            self.send("FILE_NOT_FOUND", address)
            return
        else:
            self.send("GOOD", address)
        window_size = 3
        sequence_number = 0
        all_blocks_sent = False
        with open(file_path, 'r') as file:
            messages = file.read().splitlines()
        while not all_blocks_sent:
            try:
                for i in range(window_size):
                    message = f"{sequence_number}:{messages[sequence_number]}\n"
                    self.send(message, address)
                    sequence_number += 1
            except IndexError:
                all_blocks_sent = True
                self.send(f"{sequence_number}:END_OF_FILE", address)

            try:
                self.server_socket.settimeout(5)
                for i in range(window_size):
                    acknowledgment = self.recv()[0].decode()
                    if acknowledgment == "END":
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