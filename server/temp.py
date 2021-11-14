word_list = ["a", "b", "b", "c", "d", "f"]
serverFiles = []
clientFiles = []
for x in range(int((len(word_list) - 2))):
    if os.path.exists(f"{word_list[x+2]}"):
        serverFiles.append(x+2)
    else:
        clientFiles.append(x+2)

for x in serverFiles:
    file = open(f"{word_list[x]}", "rb")
                filesize = os.path.getsize(f"{word_list[x]}")

                # Let the client know a file is about to be sent
                conn.send(f"DOWNLOAD {word_list[x]} {filesize}".encode())

                # Continually send the file
                datas = file.read(filesize)
                while datas:
                    conn.send(datas)
                    datas = file.read(filesize)
                file.close()

for x in clientFiles:
    temp = [conn, word_list[x]]
    q.put(temp)
    time.sleep(3)

    if os.path.exists(f"{word_list[x]}"):
        file = open(f"{word_list[x]}", "rb")
        filesize = os.path.getsize(f"{word_list[x]}")

        # Let the client know a file is about to be sent
        conn.send(f"DOWNLOAD {word_list[x]} {filesize} 1".encode())
                
        # Continually send the file
        datas = file.read(filesize)
        while datas:                            
            conn.send(datas)
            datas = file.read(filesize)
        file.close()
        print(f"{word_list[x]} was upload")
        else: # Else the file couldn't be found
            conn.send(f"ERROR {word_list[x]}".encode())

