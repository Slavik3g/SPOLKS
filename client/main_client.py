import os
import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_host = '127.0.0.1'
server_port = 12344

client_socket.connect((server_host, server_port))
print(f"Подключено к серверу {server_host}:{server_port}")

while True:
    command = input("Введите команду (ECHO, TIME, UPLOAD, DOWNLOAD, CLOSE): ")

    client_socket.send(command.encode())

    if command in ["CLOSE", "EXIT", "QUIT"]:
        response = client_socket.recv(1024).decode()
        print(response)
        break
    elif command == "ECHO":
        echo_message = input("Введите сообщение для отправки: ")
        client_socket.send(echo_message.encode())
        response = client_socket.recv(1024).decode()
        print(response)
    elif command == "UPLOAD":
        file_name = input("Введите имя файла для загрузки: ")
        client_socket.send(file_name.encode())

        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            client_socket.send(str(file_size).encode())
            exist_size = int(client_socket.recv(1024).decode())
            with open(file_name, 'rb') as file:
                file.seek(exist_size)
                for data in iter(lambda: file.read(1024), b''):
                    client_socket.send(data)
            print(f"Файл '{file_name}' загружен на сервер")
        else:
            print("Файл не найден")

    elif command == "DOWNLOAD":
        file_name = input("Введите имя файла для скачивания: ")
        client_socket.send(file_name.encode())

        file_size = int(client_socket.recv(1024).decode())

        if file_size > 0:
            with open(file_name, 'wb') as file:
                bytes_received = 0
                while bytes_received < file_size:
                    data = client_socket.recv(1024)
                    file.write(data)
                    bytes_received += len(data)
            print(f"Файл '{file_name}' скачан с сервера")
        else:
            print("Файл не найден на сервере")
    elif command == "TIME":
        response = client_socket.recv(1024).decode()
        print(response)

client_socket.close()