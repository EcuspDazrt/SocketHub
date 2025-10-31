import socket
import threading

HEADER = 64
PORT = 5050
# more efficient to use this to universally get the ip address of any computer
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
CONNECTIONS_MESSAGE = "!CONNECTIONS"
ACCEPT_MESSAGE = "!ACCEPT"
FILE_MESSAGE = "!FILE"

requestAccept = False

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
clients = {}
pending_files = {}
num_pending_files = 0
num_accepted = 0

def broadcast(message, sender_addr, user):
    for addr, conn in clients.items():
        if addr != sender_addr:
            try:
                data = message.encode(FORMAT)
                header = f"MSG|{len(message)}||".encode(FORMAT)
                conn.sendall(header + data)
            except:
                conn.close()
                del clients[addr]
                print(f"{user} disconnected")

def broadcast_file(filename, filesize, f, user, sender_addr):
    # num_pending_files += 1
    for addr, conn in clients.items():
        if addr != sender_addr:
            try:
                message = f"{user} is trying to share {filename} with you. \nEnter '{ACCEPT_MESSAGE}' to receive the file".encode(FORMAT)
                header = f"MSG|{len(message)}||".encode(FORMAT)
                conn.send(header + message)
            except:
                conn.close()
                del clients[addr]

def handle_client(conn, addr):
    print(f"[NEW CONNETION] {addr} connected.")
    clients[addr] = conn
    user = " "
    userSent = False
    connected = True
    while connected:
        try:
            header = b""
            while not header.endswith(b"||"):
                chunk = conn.recv(1)
                if not chunk:
                    raise ConnectionResetError    
                header += chunk

            header = header[:-2].decode(FORMAT)
            parts = header.split("|")
            data_type = parts[0]

            if data_type == "MSG":
                msg_length = int(parts[1])
                message = conn.recv(msg_length).decode(FORMAT)
                
                if message == DISCONNECT_MESSAGE:
                    print(f"{user} disconnected.")
                    connected = False
                    break

                if message == CONNECTIONS_MESSAGE:
                    conn.send((f"There are {getConnections()} connections.").encode(FORMAT))

                if message.startswith(ACCEPT_MESSAGE):
                    # num_accepted += 1
                    # if num_accepted <= (num_pending_files - 1) * getConnections():
                    #     del pending_files[0]

                    parts = message.split(" ")
                    if len(parts) < 2:
                        receive_message = f"Usage: {ACCEPT_MESSAGE} <filename>".encode(FORMAT)
                        receive_header = f"MSG|{len(receive_message)}||".encode(FORMAT)
                        conn.sendall(receive_header + receive_message)
                        continue

                    filename = parts[1]
                    if filename not in pending_files:
                        interuption_message = "That file is no longer available or does not exist.".encode(FORMAT)
                        interuption_header = f"MSG|{len(interuption_message)}||".encode(FORMAT)
                        conn.sendall(interuption_header + interuption_message)
                        continue

                    sender, filepath, filesize = pending_files[filename]
                    msg = f"Receiving '{filename}' ({filesize} bytes) from {sender}."
                    msg_data = msg.encode(FORMAT)
                    msg_header = f"MSG|{len(msg_data)}||".encode(FORMAT)
                    conn.sendall(msg_header + msg_data)

                    header = f"FILE|{filesize}|{filename}||".encode(FORMAT)
                    conn.sendall(header)

                    with open (filename, "rb") as f:
                        while True:
                            bytes_read = f.read(1024)
                            if not bytes_read:
                                break
                            conn.sendall(bytes_read)

                    # print(f"Sent '{filename}' to {addr}")
                if userSent:
                    print(f"[{user}] {message}")
                    broadcast(f"{user}: {message}", addr, user)

                if not userSent:
                    user = message
                    userSent = True
            if data_type == "FILE":
                filesize = int(parts[1])
                filename = parts[2]
                receive_file(conn, filename, filesize, user, addr)
        except ConnectionResetError:
            print(f"{user} disconnected.")
            break
        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    if addr in clients:
        del clients[addr]
    try:
        conn.close()
    except:
        pass
    

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def getConnections():
    return threading.active_count() - 1

def receive_file(conn, filename, filesize, user, addr):
    filepath = f"server_files/{filename}"
    print(filepath)
    with open(filename, "wb") as f:
        bytes_read = 0
        while bytes_read < filesize:
            chunk = conn.recv(1024)
            if not chunk:
                break
            f.write(chunk)
            bytes_read += len(chunk)
        print(f"Recieved file from {user}: {filename}")
        pending_files[filename] = (user, filepath, filesize)
        broadcast_file(filename, filesize, f, user, addr)
        # num_pending_files += 1

print("[STARTING] Server is starting...")
start()