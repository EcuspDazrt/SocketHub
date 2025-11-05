import socket
import threading
import os
import traceback

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.208.136"
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def receive():
    while True:
        try:
            header = b""
            while not header.endswith(b"||"):
                chunk = client.recv(1)
                if chunk:
                    header += chunk

            header = header[:-2].decode(FORMAT)
            print(header)
            parts = header.split("|")

            data_type = parts[0]
            length = int(parts[1])

            match data_type:
                case "MSG":
                    message = client.recv(length).decode(FORMAT)
                    print(message)
                case "FILE":
                    filename = parts[2]
                    receive_file(client, filename, length)
        except Exception:
            print("[DISCONNECTED FROM SERVER]")
            traceback.print_exc()
            client.close()
            break

def receive_file(client, filename, filesize, download_dir="downloads"):
    print("receiving file")
    os.makedirs(download_dir, exist_ok=True)

    safe_name = os.path.basename(filename)
    filepath = os.path.join(download_dir, safe_name)
    
    with open(filepath, "wb") as f:
        bytes_received = 0
        while bytes_received < filesize:
            
            chunk_size = min(2048, filesize - bytes_received)
            chunk = client.recv(chunk_size)
            if chunk:
                f.write(chunk)
                bytes_received += len(chunk)

    print(f"[DOWNLOAD COMPLETE] ({filesize} bytes) saved to {filepath}")
    return True

def send():
    while True:
        msg = input()

        if msg.startswith("!FILE"):
            filepath = msg.split(" ", 1)[1]
            send_file(filepath)
            continue
        else:
            send_message(msg)

        if msg == DISCONNECT_MESSAGE:
            client.close()
            break

def send_message(message: str):
    data = message.encode(FORMAT)
    header = f"MSG|{len(data)}||".encode(FORMAT)
    client.sendall(header + data)


def send_file(filepath):
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

        print(f"Sent file: {filename}")


        
threading.Thread(target=receive, daemon=True).start()
print("What is your username?")
send()