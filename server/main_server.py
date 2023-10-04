import os
import socket

from server import Server
from server_udp import ServerUDP

host = '192.168.120.102'
# host = '127.0.0.1'
port = 12333
udp_port = 33324

def tcp_server_communication():
    server = Server(host, port)
    server.create_server_connection()
    try:
        while True:
            server.accept_client()
            while True:
                data = server.client_socket.recv(1024).decode()
                if not data:
                    break
                if data == "ECHO":
                    server.get_msg()

                elif data == "TIME":
                    print("Пришёл запрос на получение времени")
                    server.send_time()

                elif data == "UPLOAD":
                    server.upload_to_server()

                elif data == "DOWNLOAD":
                    file_name = server.receive()
                    if os.path.exists(file_name):
                        server.download_from_server(file_name)
                    else:
                        server.send("Файл не найден")

                elif data == "CLOSE":
                    server.close_connection()
                    break

                else:
                    response = "Неверная команда. Поддерживаемые команды: ECHO, TIME, CLOSE, UPLOAD, DOWNLOAD"
                    server.send(response)

            print(f"Соединение с клиентом {server.client_address} закрыто")
    except BaseException as e:
        print(f"\nOps, error happen. Error: {e}")
    finally:
        server.close_server()


def udp_server_communication():
    server = ServerUDP(host, udp_port)
    server.create_server_connection()
    try:
        while True:
            data = server.server_socket.recvfrom(1024)
            command = data[0].decode().upper()
            address = data[1]
            if data == "CONTROL":
                server.send("CONTROL", address)
            elif command == "TIME":
                print("Пришёл запрос на получение времени")
                server.send_time(address)
            elif command == "UPLOAD":
                print("Пришёл загрузку файла на сервер")
                server.upload_file()
            elif command == "DOWNLOAD":
                file_name = server.recv()[0].decode()
                print(f"Пришёл запрос на закачку файла {file_name}")
                server.download_file(file_name, address)
    except BaseException as e:
        print(f"\nOps, error happen. Error: {e}")
    finally:
        server.close_server()

def main():
    while True:
        connections_type = input("Input connection type: ").lower()
        if connections_type == 'tcp':
            print("TCP server start")
            tcp_server_communication()
        elif connections_type == 'udp':
            print("UDP server start")
            udp_server_communication()
        else:
            print("Input error. Input TCP or UDP.")


if __name__ == '__main__':
    main()