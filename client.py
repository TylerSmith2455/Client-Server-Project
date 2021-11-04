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
        word_list = message.split()
        if not word_list:
            messageError()
        elif word_list[0] == "EXIT":
            break
        elif word_list[0] == "UPLOAD":
            conn.send(word_list[1].encode("utf-8"))
        else:
            messageError()

# Error function for communicating with server
def messageError() -> None:
    print("Please enter a valid command: UPLOAD filename or DOWNLOAD filename")
    print("Or the command: EXIT to exit the client")

# Error function for command
def commandError() -> None:
    print("Please enter the command: CONNECT server_IP_address server_port to connect to server")
    print("Or the command: EXIT to exit the client")

def main() -> None:
    while True:
        # Get command from user
        command = input("Enter Command: ")
        word_list = command.split()

        # Determine if the command is acceptable
        if not word_list:
            commandError()
        elif word_list[0] == "EXIT":
            exit()
        elif len(word_list) < 3:
            commandError()
        elif word_list[0] == "CONNECT":
            server_IP = word_list[1]
            server_port = int(word_list[2])
            conn = socket(AF_INET, SOCK_STREAM)
            conn.connect((server_IP, server_port))

            listening_thread = Thread(target=listening_fn, args=(conn,))
            talking_thread = Thread(target=talking_fn, args=(conn,))

            listening_thread.start()
            talking_thread.start()

            listening_thread.join()
            talking_thread.join()

            conn.close()
        else:
            commandError()

if __name__ == "__main__":
    main()