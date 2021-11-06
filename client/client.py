from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os


def listening_fn(conn: socket) -> None:
    while True:
        message = conn.recv(2048)
        message = message.decode('utf-8')
        word_list = message.split()
        
        if word_list[0] == "DOWNLOAD":
            filename = word_list[1]
            filesize = word_list[2]
            filesize = int(filesize)
            with open(filename, "wb") as file:
                print("I got here right here")
                data = conn.recv(filesize)
                file.write(data)
                file.close()
        elif word_list[0] == "ERROR":
            print(f"{word_list[1]} could not be found!!!")


def talking_fn(conn: socket) -> None:
    while True:
        message = input("Enter Message: ")
        word_list = message.split()
        if not word_list:
            messageError()
        elif word_list[0] == "EXIT":
            break
        #Uploads a file to the receiver if the user enters the UPLOAD keyword
        elif word_list[0] == "UPLOAD":
            #If the file exists then send it
            if os.path.exists(f"{word_list[1]}"):
                file = open(f"{word_list[1]}", "rb")
                filesize = os.path.getsize(f"{word_list[1]}")
                conn.send(f"UPLOAD {word_list[1]} {filesize}".encode())
                data = file.read()
                file.close()
                conn.sendall(data)
            else:
                print(f"{word_list[1]} could not be found")
            #conn.send(word_list[1].encode("utf-8"))
        #Deletes a file if the user enters the DELETE keyword
        elif word_list[0] == "DOWNLOAD":
            conn.send(f"DOWNLOAD {word_list[1]}".encode())

        elif word_list[0] == "DELETE":
            #If the file exists then delete it
            if os.path.exists(f"{word_list[1]}"):
                os.remove(f"{word_list[1]}")
            else:
                print(f"File {word_list[1]} could not be found")
        elif word_list[0] == "DIR":
            path = os.getcwd()
            list = os.listdir(path)
            print(f"{list}")
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