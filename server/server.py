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
                print(f"{word_list[1]} was upload")

            else: # Ask the other client for the file
                # Create a variable to store the current clients sock and requested file
                temp = [conn, word_list[1]]
                q.put(temp)
                time.sleep(1)

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
        if q.qsize() > 0:
            # Get the info from the queue
            temp = q.get()
            # If the wrong thread gets the info, put it the info back into the queue and wait
            if temp[0] == conn:
                print("same socket")
                q.put(temp)
                time.sleep(1)

            else:
                # The message got to the right thread, send an UPLOAD message to the client for the file
                print(temp[1])
                print({threading.get_ident()})
                conn.send(f"UPLOAD {temp[1]}".encode())
        else:
            continue

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