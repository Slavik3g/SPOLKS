import os

from server import Server

# host = '192.168.52.102'
host = '127.0.0.1'
port = 12333


def main():
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


if __name__ == '__main__':
    main()