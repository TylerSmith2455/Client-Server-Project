from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os
import time


# Listening thread to receive messages
def listening_fn(conn: socket) -> None:
    while True:
        # Receive the message, decode, and split
        message = conn.recv(2048)
        message = message.decode('latin-1')
        word_list = message.split()
        
        # Prepare to receive a merged file
        if len(word_list) == 5:
            filename = "merged"
            filesize = word_list[0]
            filesize = int(filesize)
            file = open(filename, "wb")

            # Continually receive the file
            while True:
                conn.settimeout(1)
                try:
                    datas = conn.recv(filesize)
                except:
                    break
                conn.settimeout(None)
                # Save the file
                file.write(datas)
            file.close()
            conn.settimeout(None)

            # Split the merged file into two files
            filesize1 = int(word_list[2])
            filesize2 = int(word_list[4])
            with open("merged", "rb") as fp:
                data = fp.read(filesize1)
                with open(f"{word_list[1]}", "wb") as file:
                    file.write(data)
                data = fp.read(filesize2)
                with open(f"{word_list[3]}", "wb") as file:
                    file.write(data)

            # Remvoe the merged file and send an ACk to the server
            os.remove("merged")
            conn.send(f"ACK {word_list[3]}".encode())

        # If it is a DOWNLOAD message, prepare to receive a file
        elif word_list[0] == "DOWNLOAD":
            filename = word_list[1]
            filesize = word_list[2]
            filesize = int(filesize)
            file = open(filename, "wb")

            # Continually receive the file
            while True:
                conn.settimeout(1)
                try:
                    datas = conn.recv(filesize)
                except:
                    break
                conn.settimeout(None)
                # Save the file
                file.write(datas)
            file.close()
            conn.settimeout(None)
            print(f"{filename} was uploaded")


            # If this DOWNLOAD came from another client, send an ACK to the server
            if len(word_list) == 4: 
                time.sleep(1)
                conn.send(f"ACK {word_list[1]}".encode())
        
        # Close the connection
        elif word_list[0] == "EXIT":
            break

        # A file could not be found
        elif word_list[0] == "ERROR":
            print(f"{word_list[1]} could not be found!!!")

        # If the server asks for a file, send it if we have it
        elif word_list[0] == "UPLOAD":
            if os.path.exists(f"{word_list[1]}"):
                file = open(f"{word_list[1]}", "rb")
                filesize = os.path.getsize(f"{word_list[1]}")

                # Let the server know a file is about to be sent
                conn.send(f"UPLOAD {word_list[1]} {filesize}".encode())

                # Continually send the file
                datas = file.read(filesize)
                while datas:
                    conn.send(datas)
                    datas = file.read(filesize)
                file.close()
                print(f"{word_list[1]} was upload")

# Need to implement being able to DOWNLOAD two files 
# Start implementing the strategies for this
# Talking thread to send messages to server
def talking_fn(conn: socket) -> None:
    while True:
        # Get input from the user
        message = input("Enter Message: ")
        word_list = message.split()

        # A command must be entered
        if not word_list:
            messageError()

        # If the user wants to exit, let the server know and disconnect
        elif word_list[0] == "EXIT":
            conn.send("EXIT".encode())
            break

        #Uploads a file to the receiver if the user enters the UPLOAD keyword
        elif word_list[0] == "UPLOAD":
            #If the file exists then send it
            if os.path.exists(f"{word_list[1]}"):
                file = open(f"{word_list[1]}", "rb")
                filesize = os.path.getsize(f"{word_list[1]}")

                # Let the server know a file is about to be sent
                conn.send(f"UPLOAD {word_list[1]} {filesize}".encode())
                
                # Continually send the file
                datas = file.read(filesize)
                while datas:
                    conn.send(datas)
                    datas = file.read(filesize)
                file.close()
                print(f"{word_list[1]} was uploaded")
                
            else: # The file couldn't be found
                print(f"{word_list[1]} could not be found")
        
        # Ask the server for a file
        elif word_list[0] == "DOWNLOAD":
            if len(word_list) == 4:
                conn.send(f"DOWNLOAD {word_list[1]} {word_list[2]} {word_list[3]}".encode())
            else:
                conn.send(f"DOWNLOAD {word_list[1]}".encode())

        #Deletes a file if the user enters the DELETE keyword
        elif word_list[0] == "DELETE":
            #If the file exists then delete it
            if os.path.exists(f"{word_list[1]}"):
                os.remove(f"{word_list[1]}")
            else:
                print(f"File {word_list[1]} could not be found")

        # Print the contents of the directory
        elif word_list[0] == "DIR":
            path = os.getcwd()
            list = os.listdir(path)
            print(f"{list}")

        else: # A valid command must be entered
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
        # Try to connect to the server
        elif word_list[0] == "CONNECT":
            server_IP = word_list[1]
            server_port = int(word_list[2])
            conn = socket(AF_INET, SOCK_STREAM)
            conn.connect((server_IP, server_port))

            # Thread for listening for messages from the server
            listening_thread = Thread(target=listening_fn, args=(conn,))

            # Thread for sending messages to the server
            talking_thread = Thread(target=talking_fn, args=(conn,))

            # Start both threads
            listening_thread.start()
            talking_thread.start()

            listening_thread.join()
            talking_thread.join()

            print("conn was closed")
            conn.close()
        else:
            commandError()

if __name__ == "__main__":
    main()