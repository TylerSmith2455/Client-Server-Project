from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os

def listening_fn(conn: socket) -> None:
    while True:
        message = conn.recv(2048)
        message = message.decode('utf-8')
        word_list = message.split()

        #Uploads a file if the client sends the UPLOAD keyword
        if word_list[0] == "UPLOAD":
            print(f"{message}")
            filename = word_list[1]
            filesize = word_list[2]
            filesize = int(filesize)
            with open(filename, "wb") as file:
                print("I got here right here")
                data = conn.recv(filesize)
                file.write(data)
                file.close()
        elif word_list[0] == "DOWNLOAD":
            if os.path.exists(f"{word_list[1]}"):
                file = open(f"{word_list[1]}", "rb")
                filesize = os.path.getsize(f"{word_list[1]}")
                conn.send(f"DOWNLOAD {word_list[1]} {filesize}".encode())
                data = file.read()
                file.close()
                conn.sendall(data)
            else:
                conn.send(f"ERROR {word_list[1]}".encode())
                print(f"{word_list[1]} could not be found")
        elif word_list[0] == "EXIT":
            conn.send("EXIT".encode())
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
    def clients() -> None:
        client_sock, client_addr = server_sock.accept()
        client_thread = Thread(target=clients, args=())
        client_thread.start()
        print('Connected to: ' + client_addr[0] + ':' + str(client_addr[1]))
        listening_thread = Thread(target=listening_fn, args=(client_sock,))
       # talking_thread = Thread(target=talking_fn, args=(client_sock,))

        listening_thread.start()
       # talking_thread.start()

        listening_thread.join()
       # talking_thread.join()

        print("conn was closed")
        client_sock.close()
    clients()
    #server_sock.close()

if __name__ == "__main__":
    main("localhost", 8080)