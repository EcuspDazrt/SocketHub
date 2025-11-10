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
running = True
server = None

clients = {}
users = {}
pending_files = {}
clients_lock = threading.Lock()
users_lock = threading.Lock()

def init_server():
    global server
    SERVER = socket.gethostbyname(socket.gethostname())
    ADDR = (SERVER, PORT)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow reuse
    server.bind(ADDR)
    return server, SERVER, ADDR

def start():
    global running, server
    print("[STARTING] Server is starting...")
    server, SERVER, ADDR = init_server()
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")

    server.settimeout(1.0)
    while running:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {len(users)}")
        except socket.timeout:
            continue
        except OSError:
            server.close()
            break

    if server:
        try:
            server.close()
        except:
            pass
    server = None
    print("[SERVER STOPPED]")


def stop():
    global running, server
    with clients_lock:
        for conn in clients.values():
            try:
                conn.close()
            except:
                pass
    running = False
    try:
        if server:
            server.close()
    except:
        pass

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
    with clients_lock:
        for addr, conn in list(clients.items()):
            if addr != sender_addr:
                try:
                    data = message.encode(FORMAT)
                    header = f"MSG|{len(message)}||".encode(FORMAT)
                    conn.sendall(header + data)
                except:
                    handle_disconnect(conn, addr, user)

def broadcast_file(fname, user, sender_addr):
    with clients_lock:
        for addr, conn in list(clients.items()):
            if addr != sender_addr:
                try:
                    message = f"{user} is trying to share {fname} with you. \nPress the button to receive the file".encode(FORMAT)
                    header = f"MSG|{len(message)}||".encode(FORMAT)
                    conn.send(header + message)
                except:
                    handle_disconnect(conn, addr, user)

def send_users(conn):
    with clients_lock:
        for addr, conn in list(clients.items()):
            safe_users = {f"{a[0]}:{a[1]}": u for a, u in users.items()}
            encoded_users = json.dumps(safe_users).encode(FORMAT)
            header = f"USERS|{len(encoded_users)}|{len(users)}||".encode(FORMAT)
            try:
                conn.sendall(header + encoded_users)
            except:
                pass

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    with clients_lock:
        clients[addr] = conn
    user = " "
    userSent = False
    connected = True
    try:
        while connected:
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
                        try:
                            conn.send((f"There are {len(users)} connections.").encode(FORMAT))
                        except:
                            pass

                    if message.startswith(ACCEPT_MESSAGE):

                        parts = message.split(" ")
                        if len(parts) < 2:
                            receive_message = f"Usage: {ACCEPT_MESSAGE} <filename>".encode(FORMAT)
                            receive_header = f"MSG|{len(receive_message)}||".encode(FORMAT)
                            try:
                                conn.sendall(receive_header + receive_message)
                            except:
                                pass
                            continue

                        fname = parts[1]
                        if fname not in pending_files:
                            interuption_message = "That file is no longer available or does not exist.".encode(FORMAT)
                            interuption_header = f"MSG|{len(interuption_message)}||".encode(FORMAT)
                            try:
                                conn.sendall(interuption_header + interuption_message)
                            except:
                                pass
                            continue

                        sender, fpath, fsize = pending_files[fname]
                        msg = f"[RECEIVING FILE] '{fname}' ({fsize} bytes) from {sender}."
                        msg_data = msg.encode(FORMAT)
                        msg_header = f"MSG|{len(msg_data)}||".encode(FORMAT)
                        try:
                            conn.sendall(msg_header + msg_data)
                        except:
                            pass

                        fileName = fpath.split('\\')

                        header = f"FILE|{fsize}|{fileName[1]}||".encode(FORMAT)
                        try:
                            conn.sendall(header)
                        except:
                            pass

                        with open (fpath, "rb") as f:
                            while True:
                                bytes_read: bytes = f.read(1024)
                                if not bytes_read:
                                    break
                                try:
                                    conn.sendall(bytes_read)
                                except:
                                    pass

                    if userSent:
                        print(f"[{user}] {message}")
                        broadcast(f"{user}: {message}", addr, user)

                    if not userSent:
                        userSent = True
                        user = sanitize_username(message)
                        with users_lock:
                            users[addr] = user

                        send_users(conn)
                        if not user.strip():
                            handle_disconnect(conn, addr, user)

                if data_type == "FILE":
                    fsize: int = int(parts[1])
                    fname = parts[2]

                    os.makedirs("server_files", exist_ok=True)
                    safe_name = os.path.basename(f"{user}_{fname}")
                    print(safe_name)
                    fpath = os.path.join("server_files", safe_name)

                    print(f"[RECEIVING FILE] {fname} ({fsize} bytes) from {user}")

                    with open(fpath, "wb") as f:
                        bytes_read = 0
                        while bytes_read < fsize:
                            chunk = conn.recv(min(2048, fsize - bytes_read))
                            if not chunk:
                                break
                            f.write(chunk)
                            bytes_read += len(chunk)

                    print(f"[SAVED] {fpath} from {user}: {fname} ({fsize} bytes)")

                    pending_files[fname] = (user, fpath, fsize)
                    broadcast_file(fname, user, addr)
    except ConnectionResetError:
        print(f"{user} disconnected.")
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        handle_disconnect(conn, addr, user)

def handle_disconnect(conn, addr, user):
    with clients_lock:
        clients.pop(addr, None)
    with users_lock:
        users.pop(addr, None)
    try:
        send_users(conn)
    except:
        pass
    try:
        conn.close()
    except:
        pass

    folder = "server_files"
    for f in os.listdir(folder):
        if f.startswith(user + "_"):
            os.remove(os.path.join(folder, f))

if __name__ == "__main__":
    start()