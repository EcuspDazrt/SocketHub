import socket
import threading

HEADER = 64
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

client = None


def read_header(sock):
    data = b""
    while b"||" not in data:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionResetError("Connection closed")
        data += chunk
    return data[:-2].decode(FORMAT)  # remove '||'


def start(ip, message_callback):
    global client
    addr = (ip, PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(addr)

    def receive():
        while True:
            try:
                header = read_header(client)
                parts = header.split("|")
                dtype = parts[0]

                if dtype == "MSG":
                    msg_len = int(parts[1])
                    data = client.recv(msg_len).decode(FORMAT)
                    message_callback(data)

                elif dtype == "FILE":
                    # skip file handling for now
                    pass

            except Exception as e:
                message_callback(f"[ERROR] {e}")
                client.close()
                break

    threading.Thread(target=receive, daemon=True).start()


def send_message(msg):
    if client:
        msg_bytes = msg.encode(FORMAT)
        header = f"MSG|{len(msg_bytes)}||".encode(FORMAT)
        client.sendall(header + msg_bytes)
