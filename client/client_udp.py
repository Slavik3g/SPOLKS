import os
import socket


class ClientUDP:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __init__(self, address, port):
        self.server_host = address
        self.server_port = port

    def close_client(self):
        self.client_socket.close()

    def send(self, message:str):
        self.client_socket.sendto(message.encode(), (self.server_host, self.server_port))

    def recv(self, size = 512):
        response = self.client_socket.recvfrom(size)
        return response

    def get_time(self):
        self.send("time")
        response = self.recv()
        return response[0].decode()

    def download_file(self, file_name):
        expected_sequence_number = 0
        file_data = ""
        while True:
            data, _ = self.recv()
            received_sequence_number, message = data.decode().split(":")
            received_sequence_number = int(received_sequence_number)

            if message == "END_OF_FILE":
                print("Файл скачан.")
                acknowledgment = f"Acknowledgment for sequence number {received_sequence_number}"
                self.send(acknowledgment)
                self.send("END")
                break

            if received_sequence_number == expected_sequence_number:
                file_data += message
                acknowledgment = f"Acknowledgment for sequence number {received_sequence_number}"
                self.send(acknowledgment)

                expected_sequence_number += 1
            else:
                print("Пропущено сообщение с номером последовательности", received_sequence_number)

        with open(file_name, 'w') as file:
            file.write(file_data)

    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            print("Файл не найден")
            return
        self.send("upload")
        self.send(file_path)
        window_size = 3
        sequence_number = 0
        all_blocks_sent = False
        with open(file_path, 'r') as file:
            messages = file.read().splitlines()
        while not all_blocks_sent:
            try:
                for i in range(window_size):
                    message = f"{sequence_number}:{messages[sequence_number]}\n"
                    self.send(message)
                    sequence_number += 1
            except IndexError:
                all_blocks_sent = True
                self.send(f"{sequence_number}:END_OF_FILE")
            try:
                self.client_socket.settimeout(5)
                for i in range(window_size):
                    acknowledgment = self.recv()[0].decode()
                    if acknowledgment == "END":
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