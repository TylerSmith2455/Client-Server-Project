file = open(f"{word_list[i]}", "rb")
    filesize = os.path.getsize(f"{word_list[i]}")

    # Let the client know a file is about to be sent
    conn.send(f"DOWNLOAD {word_list[i]} {filesize}".encode())

    # Continually send the file
    datas = file.read(filesize)
    while datas:
        conn.send(datas)
        datas = file.read(filesize)
    file.close()
    print(f"{word_list[i]} was uploaded")

    # Create a variable to store the current clients sock and requested file
    temp = [conn, word_list[j]]
    q.put(temp)
    time.sleep(3)

    # If the file was found send it, if not send an error
    if os.path.exists(f"{word_list[j]}"):
        file = open(f"{word_list[j]}", "rb")
        filesize = os.path.getsize(f"{word_list[j]}")

        # Let the client know a file is about to be sent
        conn.send(f"DOWNLOAD {word_list[j]} {filesize} 1".encode())
                
        # Continually send the file
        datas = file.read(filesize)
        while datas:                            
            conn.send(datas)
            datas = file.read(filesize)
        file.close()
        print(f"{word_list[j]} was upload")
    else: # Else the file couldn't be found
        conn.send(f"ERROR {word_list[j]}".encode())