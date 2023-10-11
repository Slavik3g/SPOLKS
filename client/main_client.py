import os
import socket

from client import Client
from client_udp import ClientUDP

# server_host = '192.168.52.102'
server_host = '127.0.0.1'
server_port = 12333
udp_server_port = 33324

def tcp_client_communication():
    client = Client(server_host, server_port)
    client.create_connection()
    try:
        while True:
            command = input("Введите команду (ECHO, TIME, UPLOAD, DOWNLOAD, CLOSE): ")
            client.send(command)

            if command == "CLOSE":
                response = client.close_connection()
                print(response)
                break

            elif command == "ECHO":
                echo_message = input("Введите сообщение для отправки: ")
                response = client.send_message(echo_message)
                print(response)

            elif command == "TIME":
                response = client.get_time()
                print(response)

            elif command == "UPLOAD":
                file_name = input("Введите имя файла для загрузки на сервер: ")
                if os.path.exists(file_name):
                    client.upload_to_server(file_name)
                else:
                    print("Файл не найден")

            elif command == "DOWNLOAD":
                file_name = input("Введите имя файла для скачивания с сервера: ")
                client.download_from_server(file_name)

            else:
                response = client.receive()
                print(response)

    except BaseException:
        print(f"\nOps, error happen.")
    finally:
        client.close_connection()

def udp_client_communication():
    client = ClientUDP(server_host, udp_server_port)
    client.client_socket.settimeout(100)
    while True:
        try:
            while True:
                command = input("Введите команду (TIME, UPLOAD, DOWNLOAD, CLOSE):").upper()

                if command == 'TIME':
                    response = client.get_time()
                    print(response)
                elif command == 'UPLOAD':
                    file_path = input("Введите путь до файла: ")
                    client.upload_file(file_path)
                elif command == 'DOWNLOAD':
                    client.send(command)
                    file_name = input("Введите имя файла для скачивания с сервера: ")
                    client.send(file_name)
                    if client.recv()[0].decode() != "FILE_NOT_FOUND":
                        lines = int(client.recv()[0].decode())
                        print("Lines num:", lines)
                        client.download_file(file_name, lines)
                    else:
                        print("Файл не найден на сервере")
                elif command == 'CLOSE':
                    break
                else:
                    print("Неверная команда")
        except socket.timeout:
            client.send("CONTROL")
            if client.recv() == "CONTROL":
                continue
        except Exception as e:
            print(f"Error {e}")
        finally:
            client.close_client()
            return


def main():
    while True:
        connections_type = input("Input connection type:").lower()
        if connections_type == 'tcp':
            tcp_client_communication()
        elif connections_type == 'udp':
            udp_client_communication()
        elif connections_type == 'exit':
            break
        else:
            print("Input error. Input TCP or UDP or exit.")

if __name__ == '__main__':
    main()
