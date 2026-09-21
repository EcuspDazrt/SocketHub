
import socket, threading, os, base64, json, traceback
from collections.abc import Callable
from io import BytesIO
from PIL import Image
from base64 import b64decode

HEADER = 64
PORT = 5051
FORMAT = "utf-8"
THUMB_DIR = "downloads"
DISCONNECT_MESSAGE = "!DISCONNECT"

class Client:
    def __init__(self):
        self.first_user = None
        self._message_callback = None
        self._users = None
        self.client = None

    # <---------- Initialization ----------->
    def start(self, ip: str, message_callback: Callable, display_users: Callable) -> None:
        self.first_user = "Anonymous"
        self._message_callback = message_callback
        self._users = display_users
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = (ip, PORT)

        try:
            self.client.connect(addr)
        except Exception as e:
            if self._message_callback:
                self._message_callback(f"[ERROR] Could not connect to {ip}: {e}")
            return

        if self._message_callback:
            self._message_callback("[CONNECTED]")
        threading.Thread(target=self.receive, daemon=True).start()


    # <---------- Utility ---------->
    @staticmethod
    def read_header(h: str) -> str:
        data = ""
        for i in range(HEADER):
            if " " not in data:
                chunk = h[i]
                data += chunk
        header = data[:-1]
        return header

    @staticmethod
    def pad_header(header: str) -> str:
        if len(header) > HEADER:
            raise Exception('header is too long.')
        header += b" " * (HEADER - len(header))
        return header


    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self.client.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("connection closed")
            buf.extend(chunk)
        return bytes(buf)



    # <---------- Sending functions ---------->
    def send_message(self, msg: str) -> None:
        if self.client:
            msg_bytes = msg.encode(FORMAT)
            header = f"MSG|{len(msg_bytes)}".encode(FORMAT)
            header = self.pad_header(header)
            self.client.sendall(header + msg_bytes)


    def send_thumbnail(self, file_path: str, file_name: str) -> None:
        try:
            img = Image.open(file_path)
            img.thumbnail((150, 150))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            thumb_data = base64.b64encode(buffer.getvalue())
            header = f"THUMB|{len(thumb_data)}|{file_name}".encode(FORMAT)
            header = self.pad_header(header)
            self.client.sendall(header + thumb_data)
        except Exception as e:
            if self._message_callback:
                self._message_callback(f"[ERROR] Preview creation failed: {e}")


    def send_file(self, file_path: str) -> None:
        if self.client and os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            ext = os.path.splitext(file_name)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                self.send_thumbnail(file_path, file_name)

            header = f"FILE|{file_size}|{file_name}".encode(FORMAT)
            header = self.pad_header(header)
            self.client.sendall(header)

            with open(file_path, "rb") as f:
                while True:
                    bytes_read = f.read(1024)
                    if not bytes_read:
                        break
                    self.client.sendall(bytes_read)

                self._message_callback(f"[SENT FILE] {file_name}")



    # <---------- Receiving functions ----------->
    def display_data(self, separated_header: list) -> None:
        data_type = separated_header[0]
        length = int(separated_header[1])
        match data_type:
            case "MSG":
                message = self._recv_exact(length).decode(FORMAT)
                self._message_callback(message)

            case "THUMB":
                file_name = separated_header[2]
                data = self._recv_exact(length)
                try:
                    thumb_bytes = b64decode(data)  # create image path
                    os.makedirs(THUMB_DIR, exist_ok=True)
                    thumb_path = os.path.join(THUMB_DIR, os.path.basename(file_name) + "_thumb.png")

                    with open(thumb_path, "wb") as f:  # write thumbnail into new file
                        f.write(thumb_bytes)

                    self._message_callback(f"[THUMBNAIL] {file_name}|{thumb_path}")  # show user thumbnail is downloaded
                except Exception as e:
                    self._message_callback(f"[ERROR] Thumbnail failed: {e}")

            case "FILE":
                file_name = separated_header[2]
                self.receive_file(file_name, length)

            case "USERS":
                users = self._recv_exact(length).decode(FORMAT)
                users_dict = json.loads(users)
                self.first_user = next(iter(users_dict.values()), 'Anonymous')
                self._users(users_dict)


    def receive(self) -> None:
        while True:
            try:
                h = self._recv_exact(HEADER)
                header = self.read_header(h.decode(FORMAT))
                separated_header = header.split("|")

                self.display_data(separated_header)

            except Exception as e:
                if self._message_callback:
                    self._message_callback(f"[DISCONNECTED] {e}")
                try:
                    self.client.close()
                except:
                    pass
                break


    def receive_file(self, file_name: str, file_size: int, download_dir: str="downloads") -> None:
        os.makedirs(download_dir, exist_ok=True)
        safe_name = os.path.basename(file_name)
        file_path = os.path.join(download_dir, safe_name)
        try:
            with open(file_path, "wb") as f:
                bytes_received = 0
                while bytes_received < file_size:

                    chunk_size = min(2048, file_size - bytes_received)
                    chunk = self._recv_exact(chunk_size)
                    if chunk:
                        f.write(chunk)
                        bytes_received += len(chunk)

            if self._message_callback:
                self._message_callback(f"[DOWNLOAD COMPLETE] ({file_size} bytes) saved as {file_name}")
        except Exception as e:
            if self._message_callback:
                self._message_callback(f"[ERROR RECEIVING FILE] {e}")