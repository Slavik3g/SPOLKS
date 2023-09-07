import os
import socket
import time

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'
port = 12344

server_socket.bind((host, port))


server_socket.listen(1)
last_client = None
print(f"Сервер слушает на {host}:{port}")
try:
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Подключен клиент с адресом {client_address}")
        while True:
            data = client_socket.recv(1024).decode()

            if not data:
                break

            if data == "ECHO":
                echo_data = client_socket.recv(1024).decode()
                print(f"Клиент отправил сообщение {echo_data}")
                client_socket.send(f"Вы сказали: {echo_data}".encode())

            elif data == "TIME":
                current_time = time.ctime(time.time())
                print("Пришёл запрос на получение времени")
                client_socket.send(current_time.encode())

            elif data == "UPLOAD":
                file_name = client_socket.recv(1024).decode()
                file_size = int(client_socket.recv(1024).decode())

                if last_client is None or last_client[0] != client_address[0]:
                    last_client = client_address
                    client_socket.send(str(0).encode())
                    file = open(file_name, 'wb')
                else:
                    if os.path.exists(file_name):
                        exist_file_size = os.path.getsize(file_name)
                        client_socket.send(str(exist_file_size).encode())
                        file = open(file_name, 'ab')
                        file.seek(exist_file_size)
                        file_size -= exist_file_size
                    else:
                        client_socket.send(str(file_size).encode())
                        file = open(file_name, 'wb')
                bytes_received = 0
                try:
                    while bytes_received < file_size:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        file.write(data)
                        bytes_received += len(data)
                    else:
                        print(f"Файл '{file_name}' загружен на сервер")
                except socket.error as e:
                    print(f"Произошла ошибка: {str(e)}")
                finally:
                    file.close()

            elif data == "DOWNLOAD":
                if last_client is None or last_client != client_address:
                    last_client = client_address
                else:
                    pass
                file_name = client_socket.recv(1024).decode()

                if os.path.exists(file_name):
                    file_size = os.path.getsize(file_name)
                    client_socket.send(str(file_size).encode())

                    with open(file_name, 'rb') as file:
                        for data in iter(lambda: file.read(1024), b''):
                            client_socket.send(data)

                    print(f"Файл '{file_name}' отправлен клиенту")
                else:
                    client_socket.send("Файл не найден".encode())

            elif data == "CLOSE":
                client_socket.send("Соединение закрыто.".encode())
                client_socket.close()
                break

            else:
                response = "Неверная команда. Поддерживаемые команды: ECHO, TIME, CLOSE, UPLOAD, DOWNLOAD"
                client_socket.send(response.encode())

        print(f"Соединение с клиентом {client_address} закрыто")
except Exception:
    server_socket.close()
