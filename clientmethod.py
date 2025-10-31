import socket
import threading

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

def start(ip):
    addr = (ip, PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(addr)
    print("hi")


    def receive():
        while True:
            try:
                msg = client.recv(2048).decode(FORMAT)
                if msg:
                    print(msg)
            except:
                print("[DISCONNECTED FROM SERVER]")
                client.close()
                break


    def send():
        while True:
            msg = input()
            message = msg.encode(FORMAT)
            msg_length = len(message)
            send_length = str(msg_length).encode(FORMAT)
            send_length += b' ' * (HEADER - len(send_length))
            client.send(send_length)
            client.send(message)

            if msg == DISCONNECT_MESSAGE:
                client.close()
                break


    threading.Thread(target=receive, daemon=True).start()
    send()