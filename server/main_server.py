import os
import socket
import time

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'
port = 12344

server_socket.bind((host, port))

server_socket.listen(1)
last_client = None
fatal_disconnect = False

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

                if last_client[0] == client_address[0] and fatal_disconnect is True:
                    fatal_disconnect = False
                    if os.path.exists(file_name):
                        exist_file_size = os.path.getsize(file_name)
                        client_socket.send(str(exist_file_size).encode())
                        file = open(file_name, 'ab')
                        file.seek(exist_file_size)
                        file_size -= exist_file_size
                    else:
                        client_socket.send(str(file_size).encode())
                        file = open(file_name, 'wb')
                else:
                    fatal_disconnect = False
                    last_client = client_address
                    client_socket.send(str(0).encode())
                    file = open(file_name, 'wb')
                bytes_received = 0
                try:
                    start_time = time.time()
                    while bytes_received < file_size:
                        data = client_socket.recv(1024)
                        if not data:
                            fatal_disconnect = True
                            break
                        file.write(data)
                        bytes_received += len(data)
                    else:
                        end_time = time.time()
                        elapsed_time = end_time - start_time
                        bitrate = (file_size * 8) / (elapsed_time * 1024 * 1024)
                        print(f"Файл '{file_name}' загружен на сервер.")
                        client_socket.send(f"Битрейт: {bitrate:.2f} Mbps".encode())

                except socket.error as e:
                    print(f"Произошла ошибка: {str(e)}")
                    fatal_disconnect = True
                finally:
                    file.close()

            elif data == "DOWNLOAD":
                file_name = client_socket.recv(1024).decode()
                if os.path.exists(file_name):
                    if last_client is not None and last_client[0] == client_address[0] and fatal_disconnect is True:
                        fatal_disconnect = False
                        client_socket.send("Докачка файла".encode())
                        client_socket.send(str(os.path.getsize(file_name)).encode())
                        file = open(file_name, 'rb')
                        file_offset = int(client_socket.recv(1024).decode())
                        file.seek(file_offset)
                    else:
                        fatal_disconnect = False
                        last_client = client_address
                        client_socket.send(str(os.path.getsize(file_name)).encode())
                        file = open(file_name, 'rb')
                    try:
                        for data in iter(lambda: file.read(1024), b''):
                            client_socket.send(data)
                        print(f"Файл '{file_name}' отправлен клиенту")
                    except Exception:
                        print("Клиент отключился")
                        fatal_disconnect = True
                        break
                    finally:
                        file.close()
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
except BaseException as e:
    print(f"\nOps, error happen. Error: {e}")
finally:
    server_socket.close()
