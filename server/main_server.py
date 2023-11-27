import os

from server import Server

# host = '192.168.52.102'
host = '127.0.0.1'
port = 12334


def main():
    server = Server(host, port)
    server.create_server_connection()
    try:
        while True:
            server.start_server()
    except BaseException as e:
        pass
    finally:
        server.close_server()


if __name__ == '__main__':
    main()