from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread


def listening_fn(conn: socket) -> None:
    while True:
        message = conn.recv(2048)
        print(f"[CLIENT] {message.decode('utf-8')}")
        if message.decode("utf-8") == "exit":
            break


def talking_fn(conn: socket) -> None:
    while True:
        message = input("Enter Message: ")
        conn.send(message.encode("utf-8"))
        if message == "exit":
            break


def main(hostname: str, portno: int) -> None:
    server_sock = socket(AF_INET, SOCK_STREAM)
    server_sock.bind((hostname, portno))
    server_sock.listen()
    client_sock, client_addr = server_sock.accept()

    listening_thread = Thread(target=listening_fn, args=(client_sock,))
    talking_thread = Thread(target=talking_fn, args=(client_sock,))

    listening_thread.start()
    talking_thread.start()

    listening_thread.join()
    talking_thread.join()

    client_sock.close()
    server_sock.close()


if __name__ == "__main__":
    main("localhost", 8080)