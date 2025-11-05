import socket
import threading
import traceback
import os

HEADER = 64
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

client = None
_callback = None


def start(ip, message_callback):
    global client, _callback
    _callback = message_callback
    addr = (ip, PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect(addr)
        if _callback:
            _callback(f"[CONNECTED] Connected to {ip}")
    except Exception as e:
        if _callback:
            _callback(f"[ERROR] Could not connect to {ip}: {e}")
        return

    def receive():
        while True:
            try:
                header = b""
                while not header.endswith(b"||"):
                    chunk = client.recv(1)
                    if chunk:
                        header += chunk

                header = header[:-2].decode(FORMAT)
                parts = header.split("|")

                data_type = parts[0]
                length = int(parts[1])

                match data_type:
                    case "MSG":
                        message = client.recv(length).decode(FORMAT)
                        _callback(message)
                    case "FILE":
                        filename = parts[2]
                        receive_file(client, filename, length)

            except Exception as e:
                if _callback:
                    _callback(f"[DISCONNECTED] {e}")
                try:
                    client.close()
                except:
                    pass
                break

    threading.Thread(target=receive, daemon=True).start()

def send_message(msg):
    if client:
        msg_bytes = msg.encode(FORMAT)
        header = f"MSG|{len(msg_bytes)}||".encode(FORMAT)
        client.sendall(header + msg_bytes)

def send_file(filepath):
    if client and os.path.exists(filepath):
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        header = f"FILE|{filesize}|{filename}||".encode(FORMAT)
        client.sendall(header)

        with open(filepath, "rb") as f:
            while True:
                bytes_read = f.read(1024)
                if not bytes_read:
                    break
                client.sendall(bytes_read)

            _callback(f"[SENT FILE] {filename}")

def receive_file(client, filename, filesize, download_dir="downloads"):
    _callback(f"[RECEIVING FILE] {filename}")
    os.makedirs(download_dir, exist_ok=True)

    safe_name = os.path.basename(filename)
    filepath = os.path.join(download_dir, safe_name)
    try:
        with open(filepath, "wb") as f:
            bytes_received = 0
            while bytes_received < filesize:

                chunk_size = min(2048, filesize - bytes_received)
                chunk = client.recv(chunk_size)
                if chunk:
                    f.write(chunk)
                    bytes_received += len(chunk)

        if _callback:
            _callback(f"[DOWNLOAD COMPLETE] ({filesize} bytes) saved to {filepath}")
    except Exception as e:
        if _callback:
            _callback(f"[ERROR RECEIVING FILE] {e}")
    return True
