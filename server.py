import socket
import threading
import os
import re
import json

HEADER = 64
PORT = 5051
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
CONNECTIONS_MESSAGE = "!CONNECTIONS"
ACCEPT_MESSAGE = "!ACCEPT"
FILE_MESSAGE = "!FILE"

requestAccept = False

clients = {}
users = {}
pending_files = {}

def init_server():
    SERVER = socket.gethostbyname(socket.gethostname())
    ADDR = (SERVER, PORT)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    return server, SERVER, ADDR

def start():
    print("[STARTING] Server is starting...")
    server, SERVER, ADDR = init_server()
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {len(users)}")

def sanitize_username(name: str) -> str:
    # No escape characters
    name = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', name)
    # No control characters (ASCII < 32 or DEL = 127)
    name = ''.join(ch for ch in name if 32 <= ord(ch) <= 126)
    # limit length
    return name[:20]

def read_header(conn):
    data = b""
    while b"||" not in data:
        chunk = conn.recv(1)
        if not chunk:
            raise ConnectionResetError("Connection closed while reading header")
        data += chunk
    # Split off the '||'
    header = data[:-2].decode('utf-8')
    return header

def broadcast(message, sender_addr, user):
    for addr, conn in clients.items():
        if addr != sender_addr:
            try:
                data = message.encode(FORMAT)
                header = f"MSG|{len(message)}||".encode(FORMAT)
                conn.sendall(header + data)
            except:
                handle_disconnect(conn, addr, user)

def broadcast_file(filename, user, sender_addr):
    for addr, conn in clients.items():
        if addr != sender_addr:
            try:
                message = f"{user} is trying to share {filename} with you. \nPress the button to receive the file".encode(FORMAT)
                header = f"MSG|{len(message)}||".encode(FORMAT)
                conn.send(header + message)
            except:
                handle_disconnect(conn, addr, user)

def send_users(conn):
    for addr, conn in clients.items():
        safe_users = {f"{a[0]}:{a[1]}": u for a, u in users.items()}
        encoded_users = json.dumps(safe_users).encode(FORMAT)
        header = f"USERS|{len(encoded_users)}|{len(users)}||".encode(FORMAT)
        conn.sendall(header + encoded_users)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    clients[addr] = conn
    user = " "
    userSent = False
    connected = True
    while connected:
        try:
            send_users(conn)
            header = read_header(conn)
            parts = header.split("|")
            data_type = parts[0]

            if data_type == "MSG":
                msg_length = int(parts[1])
                message = conn.recv(msg_length).decode(FORMAT)
                
                if message == DISCONNECT_MESSAGE:
                    print(f"{user} disconnected.")
                    handle_disconnect(conn, addr, user)
                    connected = False
                    break

                if message == CONNECTIONS_MESSAGE:
                    conn.send((f"There are {len(users)} connections.").encode(FORMAT))

                if message.startswith(ACCEPT_MESSAGE):

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
                    msg = f"[RECEIVING FILE] '{filename}' ({filesize} bytes) from {sender}."
                    msg_data = msg.encode(FORMAT)
                    msg_header = f"MSG|{len(msg_data)}||".encode(FORMAT)
                    conn.sendall(msg_header + msg_data)

                    fileName = filepath.split('\\')

                    header = f"FILE|{filesize}|{fileName[1]}||".encode(FORMAT)
                    conn.sendall(header)

                    with open (filepath, "rb") as f:
                        while True:
                            bytes_read: bytes = f.read(1024)
                            if not bytes_read:
                                break
                            conn.sendall(bytes_read)

                if userSent:
                    print(f"[{user}] {message}")
                    broadcast(f"{user}: {message}", addr, user)

                if not userSent:
                    userSent = True
                    user = sanitize_username(message)
                    users[addr] = user

                    send_users(conn)
                    if not user.strip():
                        handle_disconnect(conn, addr, user)

            if data_type == "FILE":
                filesize: int = int(parts[1])
                filename = parts[2]
                
                os.makedirs("server_files", exist_ok=True)
                safe_name = os.path.basename(f"{user}_{filename}")
                print(safe_name)
                filepath = os.path.join("server_files", safe_name)

                print(f"[RECEIVING FILE] {filename} ({filesize} bytes) from {user}")

                with open(filepath, "wb") as f:
                    bytes_read = 0
                    while bytes_read < filesize:
                        chunk = conn.recv(min(2048, filesize - bytes_read))
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_read += len(chunk)

                print(f"[SAVED] {filepath} from {user}: {filename} ({filesize} bytes)")

                pending_files[filename] = (user, filepath, filesize)
                broadcast_file(filename, user, addr)
        except ConnectionResetError:
            print(f"{user} disconnected.")
            break
        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    if addr in clients:
        del clients[addr]
        del users[addr]
        send_users(conn)
    try:
        handle_disconnect(conn, addr, user)
    except:
        pass

def handle_disconnect(conn, addr, user):
    del clients[addr]
    del users[addr]
    send_users(conn)
    conn.close()

    folder = "server_files"
    for f in os.listdir(folder):
        if f.startswith(user + "_"):
            os.remove(os.path.join(folder, f))

if __name__ == "__main__":
    start()