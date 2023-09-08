import os
import socket

from utils.progress_bar import progress

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_host = '127.0.0.1'
server_port = 12344

client_socket.connect((server_host, server_port))
print(f"Подключено к серверу {server_host}:{server_port}")
try:
    while True:
        command = input("Введите команду (ECHO, TIME, UPLOAD, DOWNLOAD, CLOSE): ")

        client_socket.send(command.encode())

        if command == "CLOSE":
            response = client_socket.recv(1024).decode()
            print(response)
            break

        elif command == "ECHO":
            echo_message = input("Введите сообщение для отправки: ")
            client_socket.send(echo_message.encode())
            response = client_socket.recv(1024).decode()
            print(response)

        elif command == "TIME":
            response = client_socket.recv(1024).decode()
            print(response)

        elif command == "UPLOAD":
            file_name = input("Введите имя файла для загрузки на сервер: ")
            client_socket.send(file_name.encode())

            if os.path.exists(file_name):
                file_size = os.path.getsize(file_name)
                client_socket.send(str(file_size).encode())
                sent_size = int(client_socket.recv(1024).decode())
                with open(file_name, 'rb') as file:
                    file.seek(sent_size)
                    for data in iter(lambda: file.read(1024), b''):
                        progress(sent_size, file_size)
                        sent_size += len(data)
                        client_socket.send(data)
                print(f"\nФайл '{file_name}' загружен на сервер")
                bitrate = client_socket.recv(1024).decode()
                print(bitrate)
            else:
                print("Файл не найден")

        elif command == "DOWNLOAD":
            file_name = input("Введите имя файла для скачивания с сервера: ")
            client_socket.send(file_name.encode())
            response = str(client_socket.recv(1024).decode())
            if response == "Файл не найден":
                print("Файл не найден на сервере")
            else:
                if response == "Докачка файла":
                    print(f"Будет произведена докачка файла с сервера")
                    file_size = int(client_socket.recv(1024).decode())
                    curr_file_size = os.path.getsize(file_name)
                    client_socket.send(str(curr_file_size).encode())
                    file_size -= curr_file_size
                    file = open(file_name, "ab")
                else:
                    file_size = int(response)
                    file = open(file_name, "wb")

                bytes_received = 0
                try:
                    while bytes_received < file_size:
                        progress(bytes_received, file_size)
                        data = client_socket.recv(1024)
                        file.write(data)
                        bytes_received += len(data)
                    print(f"\nФайл '{file_name}' скачан с сервера")
                finally:
                    file.close()

        else:
            response = client_socket.recv(1024).decode()
            print(response)
except BaseException:
    print(f"\nOps, error happen.")
finally:
    client_socket.close()
