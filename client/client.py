from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os
import time
import sys


# Listening thread to receive messages
def listening_fn(conn: socket) -> None:
    while True:
        # Receive the message, decode, and split
        message = conn.recv(2048)
        message = message.decode('latin-1')
        word_list = message.split()
        
        # Prepare to receive a merged file
        if len(word_list) > 4:
            filename = "merged"
            filesize = word_list[0]
            filesize = int(filesize)
            file = open(filename, "wb")

            # Continually receive the file
            while True:
                conn.settimeout(3)
                try:
                    datas = conn.recv(filesize)
                except:
                    break
                conn.settimeout(None)
                # Save the file
                file.write(datas)
            file.close()
            conn.settimeout(None)
            
            index = 1

            # Split the merged files into the right files
            with open("merged", "rb") as fp:
                for x in range(int((len(word_list)-1)/2)):
                    data = fp.read(int(word_list[index+1]))
                    with open(f"{word_list[index]}", "wb") as file:
                        file.write(data)
                    print(f"{word_list[index]} was uploaded")
                    index += 2

            # Remove the merged file
            os.remove("merged")

            conn.send(f"ACK".encode())

        # If it is a DOWNLOAD message, prepare to receive a file
        elif word_list[0] == "DOWNLOAD":
            filename = word_list[1]
            filesize = word_list[2]
            filesize = int(filesize)
            file = open(filename, "wb")

            # Continually receive the file
            while True:
                conn.settimeout(3)
                try:
                    datas = conn.recv(filesize)
                except:
                    break
                conn.settimeout(None)
                # Save the file
                file.write(datas)

            file.close()
            conn.settimeout(None)

            # Send ACK to server
            conn.send(f"ACK".encode())

            print(f"{filename} was uploaded")
        
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
                print(f"{word_list[1]} was uploaded")


              
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
                
                data_rate_start = time.time()

                # Continually send the file
                datas = file.read(64000)
                temp = datas
                while datas:
                    conn.send(datas)
                    datas = file.read(64000)
                    temp += datas
                    # Compute data download rate
                    if (time.time() - data_rate_start) > 1:
                        rateFile = open("ClientUploadRate.txt", "a")
                        rate = sys.getsizeof(temp)/((time.time()-data_rate_start)*1024*1024)
                        rateFile.write(f"Client uploading at {rate} MB/sec \n")
                        rateFile.close()
                        temp = datas
                        data_rate_start = time.time()
                file.close()
                
                print(f"{word_list[1]} was uploaded")
                
            else: # The file couldn't be found
                print(f"{word_list[1]} could not be found")
        
        # Ask the server for a file or multipe files
        elif word_list[0] == "DOWNLOAD":
            if len(word_list) > 3:
                conn.send(f"{message}".encode())
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

            print("Disconnected from server")
            conn.close()
        else:
            commandError()

if __name__ == "__main__":
    main()