import os

from client import Client


# server_host = '192.168.52.102'
server_host = '127.0.0.1'
server_port = 12334


def main():
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


if __name__ == '__main__':
    main()
