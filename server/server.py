import socket
import threading
from queue import Queue
import os
import time

# Thread for receiving messages from the client
def listening_fn(conn: socket, q) -> None:
    while True:
        # Receive the message, decode, and split
        message = conn.recv(2048)
        message = message.decode('latin-1')
        word_list = message.split()

        #Uploads a file if the client sends the UPLOAD keyword
        if word_list[0] == "UPLOAD":
            print(f"{message}")
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
        
        # Scenerio 2, client is asking for multiple files
        elif len(word_list) > 3:
            serverFiles = []
            clientFiles = []

            # Find which files the server already has
            for x in range(int((len(word_list) - 2))):
                if os.path.exists(f"{word_list[x+2]}"):
                    serverFiles.append(x+2)
                else:
                    clientFiles.append(x+2)

            # Strategy 1, send the files one at a time
            if word_list[1] == "1":
                
                # For every file that the server has, send it
                for x in serverFiles:
                    file = open(f"{word_list[x]}", "rb")
                    filesize = os.path.getsize(f"{word_list[x]}")

                    # Let the client know a file is about to be sent
                    conn.send(f"DOWNLOAD {word_list[x]} {filesize}".encode())
                    print(f"Sending {word_list[x]}")

                    # Continually send the file
                    datas = file.read(filesize)
                    while datas:
                        conn.send(datas)
                        datas = file.read(filesize)
                    file.close()

                    # Wait for ACK from client
                    message = conn.recv(2048)
                    message = message.decode('latin-1')
                    if message == "ACK":
                        print("ACK received")

                # For every file the server doesn't have
                for x in clientFiles:
                    # See if the other client has the file
                    temp = [conn, word_list[x]]
                    q.put(temp)

                    # Give the client time to upload the file
                    for a in range(3):
                        time.sleep(a+2)
                        if os.path.exists(f"{word_list[x]}"):
                            break
        
                    flag = 0
                    # If the other client sent the file
                    if os.path.exists(f"{word_list[x]}"):
                        file = open(f"{word_list[x]}", "rb")
                        filesize = os.path.getsize(f"{word_list[x]}")

                        # Let the client know a file is about to be sent
                        conn.send(f"DOWNLOAD {word_list[x]} {filesize} 1".encode())
                
                        # Continually send the file
                        # Let the other thread continue to download the file
                        while True:
                            datas = file.read(filesize)
                            while datas:                            
                                conn.send(datas)
                                datas = file.read(filesize)
                                flag = 0
                            if flag == 0:
                                flag = 1
                                time.sleep(1)
                            else:
                                break
                        file.close()

                        # Wait for ACK from client
                        print(f"{word_list[x]} was upload")
                        message = conn.recv(2048)
                        message = message.decode('latin-1')
                        if message == "ACK":
                            print("ACK received")
                        os.remove(f"{word_list[x]}")
                        

                    else: # Else the file couldn't be found
                        conn.send(f"ERROR {word_list[x]}".encode())

            # Strategy 2, wait until the file is received from the other client and merge them
            elif word_list[1] == "2":
                sentFiles = []
                data = b""
                flag = 0

                # For every file the server doesn't have, see if the other client has it
                for x in clientFiles:
                    temp = [conn, word_list[x]]
                    q.put(temp)

                    # Give the other client time to send the file
                    for a in range(3):
                        time.sleep(a+2)
                        if os.path.exists(f"{word_list[x]}"):
                            break
                    
                    # If the other client sent the file
                    if os.path.exists(f"{word_list[x]}"):
                        file = open(f"{word_list[x]}", "rb")
                        sentFiles.append(x)
                        while True:
                            datas = file.read()
                            while datas:                            
                                data += datas
                                datas = file.read()
                                flag = 0
                            if flag == 0:
                                flag = 1
                                time.sleep(1)
                            else:
                                break
                        file.close()
                    else:
                        conn.send(f"ERROR {word_list[x]}".encode())


                # Add all the server files to the data variable
                for x in serverFiles:
                    sentFiles.append(x)
                    with open(f'{word_list[x]}', "rb") as fp:
                        data2 = b""
                        data2 = fp.read()
                    data += data2

                # Write all the data to one file
                with open ('merged', 'wb') as fp:
                        fp.write(data)

                # Let the client know a merged file is about to be sent
                mergedSize = os.path.getsize("merged")
                message = f"{mergedSize}"

                for x in sentFiles:
                    filesize = os.path.getsize(f"{word_list[x]}")
                    message += f" {word_list[x]} {filesize}"

                # Remove all the files that came from the other client
                for x in clientFiles:
                    if os.path.exists(f"{word_list[x]}"):
                        os.remove(f"{word_list[x]}")
                
                conn.send(f"{message}".encode())

                file = open('merged', "rb")

                # Continually send the file
                datas = file.read(filesize)
                while datas:                            
                    conn.send(datas)
                    datas = file.read(filesize)
                file.close()

                os.remove("merged")

            # Strategy 3, server waits for both files to be ready and sends them back to back
            elif word_list[1] == "3":

                # For every file the server doesn't have, see if the other client has it
                for x in clientFiles:
                    # See if the other client has the file
                    temp = [conn, word_list[x]]
                    q.put(temp)

                    # Give the client time to upload the file
                    for a in range(3):
                        time.sleep(a+2)
                        if os.path.exists(f"{word_list[x]}"):
                            break
                    
                    # If the client sent the file
                    if os.path.exists(f"{word_list[x]}"):
                        file = open(f"{word_list[x]}", "rb")
                        filesize = os.path.getsize(f"{word_list[x]}")

                        # Let the client know a file is about to be sent
                        conn.send(f"DOWNLOAD {word_list[x]} {filesize}".encode())

                        # Continually send the file
                        while True:
                            datas = file.read(filesize)
                            while datas:                            
                                conn.send(datas)
                                datas = file.read(filesize)
                                flag = 0
                            if flag == 0:
                                flag = 1
                                time.sleep(2)
                            else:
                                break
                        file.close()

                        # Wait for ACK from client
                        message = conn.recv(2048)
                        message = message.decode('latin-1')
                        if message == "ACK":
                            print("ACK received")
                        print(f"{word_list[x]} was upload")
                        os.remove(f"{word_list[x]}")

                    else: # Else the file couldn't be found
                        conn.send(f"ERROR {word_list[x]}".encode())
                        time.sleep(1)

                # For every file the server has, send it
                for x in serverFiles:
                    file = open(f"{word_list[x]}", "rb")
                    filesize = os.path.getsize(f"{word_list[x]}")

                    # Let the client know a file is about to be sent
                    conn.send(f"DOWNLOAD {word_list[x]} {filesize}".encode())
                    print(f"Sending {word_list[x]}")

                    # Continually send the file
                    datas = file.read(filesize)
                    while datas:
                        conn.send(datas)
                        datas = file.read(filesize)                        
                    file.close()

                    # Wait for ACK from client
                    message = conn.recv(2048)
                    message = message.decode('latin-1')
                    if message == "ACK":
                        print("ACK received")
                
        # Send the specified file to client
        # If it isn't on the server ask the other client
        elif word_list[0] == "DOWNLOAD":
            if os.path.exists(f"{word_list[1]}"):
                file = open(f"{word_list[1]}", "rb")
                filesize = os.path.getsize(f"{word_list[1]}")

                # Let the client know a file is about to be sent
                conn.send(f"DOWNLOAD {word_list[1]} {filesize}".encode())

                # Continually send the file
                datas = file.read(filesize)
                while datas:
                    conn.send(datas)
                    datas = file.read(filesize)
                file.close()
                message = conn.recv(2048)
                message = message.decode('latin-1')
                if message == "ACK":
                    print("ACK received")
                print(f"{word_list[1]} was uploaded")

            else: # Ask the other client for the file
                # Create a variable to store the current clients sock and requested file
                temp = [conn, word_list[1]]
                q.put(temp)
                time.sleep(3)

                # If the file was found send it, if not send an error
                if os.path.exists(f"{word_list[1]}"):
                    file = open(f"{word_list[1]}", "rb")
                    filesize = os.path.getsize(f"{word_list[1]}")

                    # Let the client know a file is about to be sent
                    conn.send(f"DOWNLOAD {word_list[1]} {filesize} 1".encode())
                
                    # Continually send the file
                    datas = file.read(filesize)
                    while datas:                            
                        conn.send(datas)
                        datas = file.read(filesize)
                    file.close()
                    print(f"{word_list[1]} was upload")
                else: # Else the file couldn't be found
                    conn.send(f"ERROR {word_list[1]}".encode())

        # If the client sends an ACK, delete the requested file
        elif word_list[0] == "ACK":
            print("Got to ACK")
            if os.path.exists(f"{word_list[1]}"):
                os.remove(f"{word_list[1]}")
                print("File exists")

        # Break the connection
        elif word_list[0] == "EXIT":
            conn.send("EXIT".encode())
            break

# Talking Thread to send messages to Clients asking for files
def talking_fn(conn: socket, q) -> None:
    # Coninually check for the queue to have something in it
    while True:
        if q.empty() != 0:
            # Get the info from the queue
            temp = q.get()

            # If the wrong thread gets the info, put it the info back into the queue and wait
            if temp[0] == conn:
                print(f"wrong sock {threading.get_ident()}")
                q.put(temp)
                time.sleep(2)
            else:
                # The message got to the right thread, send an UPLOAD message to the client for the file
                print(f"UPLOAD {temp[1]}")
                conn.send(f"UPLOAD {temp[1]}".encode())

def main(hostname: str, portno: int) -> None:
    # Create a server sock
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((hostname, portno))
    server_sock.listen()

    print(hostname)

    # Create a queue for the threads to communicate through
    q = Queue()
    def clients(q) -> None:
        client_sock, client_addr = server_sock.accept()

        # After getting a new client, create a new thread to accept more clients
        client_thread = threading.Thread(target=clients, args=(q, ))
        client_thread.start()

        print('Connected to: ' + client_addr[0] + ':' + str(client_addr[1]))

        # Create talking and listening threads for each client thread
        listening_thread = threading.Thread(target=listening_fn, args=(client_sock,q, ))
        talking_thread = threading.Thread(target=talking_fn, args=(client_sock,q, ))
        
        listening_thread.start()
        talking_thread.start()
        client_thread.join()
        listening_thread.join()
        talking_thread.join()

        print("conn was closed")
        client_sock.close()
    clients(q)
    #server_sock.close()

if __name__ == "__main__":
    main(socket.gethostbyname(socket.gethostname()), 12345)