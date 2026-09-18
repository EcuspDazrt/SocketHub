import socket, threading, os, re, json

HEADER = 64
PORT = 5051
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
CONNECTIONS_MESSAGE = "!CONNECTIONS"
ACCEPT_MESSAGE = "!ACCEPT"
FILE_MESSAGE = "!FILE"

class Server:
    def __init__(self):
        self.request_accept = False
        self.running = True
        self.server = None
        self.server_address = None

        self.clients = {}
        self.users = {}
        self.pending_files = {}
        self.clients_lock = threading.Lock()
        self.users_lock = threading.Lock()


    # <---------- Base Functionality ---------->
    def init_server(self) -> None:
        """Instantiates server variables, spins up the process, and gives it an address"""
        server = socket.gethostbyname(socket.gethostname())
        self.server_address = (server, PORT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow reuse
        self.server.bind(self.server_address)


    def start(self) -> None:
        """Initiates the server process itself, closes when the main loop exits"""
        print("[STARTING] Server is starting...")
        self.init_server()
        self.server.listen()
        print(f"[LISTENING] Server is listening on {self.server_address[0]}")

        self.server.settimeout(1.0)
        while self.running:
            try:
                # accept a new client and add it to a client handling thread
                conn, addr = self.server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                thread.start()
                print(f"[ACTIVE CONNECTIONS] {len(self.users)}")
            except socket.timeout:
                continue
            except OSError:
                self.server.close()
                break

        # close server if the running loop exits
        if self.server:
            try:
                self.server.close()
            except:
                pass
        self.server = None
        print("[SERVER STOPPED]")


    def stop(self) -> None:
        """Shuts down the server. Starts by closing the connections and then cleans up the server process."""
        with self.clients_lock:
            for conn in self.clients.values(): # try to close every connection to the server
                try:
                    conn.close()
                except:
                    pass

        self.running = False # clean up server process after-wards
        try:
            if self.server:
                self.server.close()
        except:
            pass


    def handle_client(self, conn: SSLSocket, addr: tuple) -> None:
        """Main server functionality. Handles every message, thumbnail, and file transfer and decides
        whether the client stays connected to the server."""
        print(f"[NEW CONNECTION] {addr} connected.")
        with self.clients_lock:
            self.clients[addr] = conn
        username = " "
        username_sent = False
        connected = True
        try:
            while connected:
                self.send_users()
                h = conn.recv(HEADER)
                header = self.read_header(h.decode(FORMAT))
                parts = header.split("|")
                data_type = parts[0]

                if data_type == "MSG":
                    connected, username_sent = self.parse_message(parts, conn, addr, username, username_sent)

                if data_type == "THUMB":
                    self.parse_thumb(parts, conn, addr)

                if data_type == "FILE":
                    self.parse_file(parts, conn, username)

        except ConnectionResetError:
            print(f"{username} disconnected.")
        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
        finally:
            self.handle_disconnect(conn, addr, username)


    def handle_disconnect(self, conn: SSLSocket, addr: tuple, username: str) -> None:
        """Disconnects the entire server. Clears the clients and users and wipes the
        file storage."""
        with self.clients_lock:
            self.clients.pop(addr, None)
        with self.users_lock:
            self.users.pop(addr, None)
        try:
            self.send_users()
        except:
            pass
        try:
            conn.close()
        except:
            pass


        folder = "server_files"
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.startswith(username + "_"):
                    os.remove(os.path.join(folder, f))



    # <---------- General Sends ---------->
    def send_users(self) -> None:
        """Sends user status update to all connections to server."""
        with self.clients_lock:
            for addr, conn in list(self.clients.items()):
                safe_users = {f"{a[0]}:{a[1]}": u for a, u in self.users.items()}
                encoded_users = json.dumps(safe_users).encode(FORMAT)
                header = f"USERS|{len(encoded_users)}|{len(self.users)}".encode(FORMAT)
                header = self.pad_header(header)
                try:
                    conn.sendall(header + encoded_users)
                except:
                    pass


    @classmethod
    def send_message(cls, message: str | bytes, conn: SSLSocket) -> None:
        """Sends message to a single client."""
        header = f"MSG|{len(message)}".encode(FORMAT)
        header = cls.pad_header(header)
        try:
            conn.sendall(header + message)
        except:
            pass


    @classmethod
    def send_file(cls, conn: SSLSocket, file_path: str, file_name: str) -> None:
        """Sends file header before the file. Streams the file over to the intended user."""
        header = f"FILE|{file_size}|{file_name[1]}".encode(FORMAT)
        header = cls.pad_header(header)
        try:
            conn.sendall(header)
        except:
            pass

        with open(file_path, "rb") as f:
            while True:
                bytes_read: bytes = f.read(1024)
                if not bytes_read:
                    break
                try:
                    conn.sendall(bytes_read)
                except:
                    pass


    @classmethod
    def send_thumb(cls, conn: SSLSocket, length: int, filename: str, thumb_data: bytes) -> None:
        """Sends thumbnail picture with the standard header."""
        try:
            header = f"THUMB|{length}|{filename}".encode(FORMAT)
            header = cls.pad_header(header)
            conn.sendall(header + thumb_data)
        except:
            pass



    # <---------- Broadcasting ---------->
    def broadcast(self, message: str, sender_addr: tuple, username: str) -> None:
        """Sends message to all users connected to the server."""
        with self.clients_lock:
            for addr, conn in list(self.clients.items()):
                if addr == sender_addr:
                    continue
                try:
                    data = message.encode(FORMAT)
                    header = f"MSG|{len(message)}".encode(FORMAT)
                    header = self.pad_header(header)
                    conn.sendall(header + data)
                except:
                    self.handle_disconnect(conn, addr, username)


    def broadcast_file(self, file_name: str, username: str, sender_addr: tuple) -> None:
        """Sends message signaling file transfer to every connection to the server."""
        with self.clients_lock:
            for addr, conn in list(self.clients.items()):
                if addr == sender_addr:
                    continue
                self.send_message(f"{username} is trying to share {file_name} with you. \nPress the button to receive the file".encode(FORMAT), conn)



    # <----------- Misc ---------->
    @classmethod
    def sanitize_username(cls, username: str) -> str:
        """Cleans up username entries."""
        # No commands
        if username in (DISCONNECT_MESSAGE, CONNECTIONS_MESSAGE, FILE_MESSAGE, ACCEPT_MESSAGE):
            return ''
        # No escape characters
        username = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', username)
        # No control characters (ASCII < 32 or DEL = 127)
        username = ''.join(ch for ch in username if 32 <= ord(ch) <= 126)
        # limit length
        return username[:20]


    @classmethod
    def read_header(cls, h: str) -> str:
        """Parses header into usable data"""
        data = ""
        for i in range(HEADER):
            if " " in data:
                continue
            chunk = h[i]
            data += chunk
        header = data[:-1]
        return header


    @classmethod
    def pad_header(cls, header: str) -> str:
        """Adds empty characters to header so it reaches desired length"""
        if len(header) < HEADER:
            header += b" " * (HEADER - len(header))
        return header



    # <---------- Data Type Parsing ---------->
    def accept_file(self, conn: SSLSocket, message: str) -> None:
        """Processes the message that accepts file transfer.
        If it's valid, it sends the file over to the user."""
        parts = message.split(" ")
        if len(parts) < 2: # guard against incorrect acceptance usage
            self.send_message(f"Usage: {ACCEPT_MESSAGE} <filename>".encode(FORMAT), conn)

        file_name = parts[1]
        if file_name not in self.pending_files: # guard against expired or non-existent files
            self.send_message("That file is no longer available or does not exist.".encode(FORMAT), conn)

        sender_name, file_path, file_size = self.pending_files[file_name]
        self.send_message(f"[RECEIVING FILE] '{file_name}' ({file_size} bytes) from {sender_name}.", conn)

        file_name = file_path.split('\\')
        self.send_file(conn, file_path, file_name)


    def parse_message(self, parts: list, user_conn: SSLSocket, user_addr: tuple,
                      username: str, username_sent: bool) -> list[bool]:
        """Parses a message sent to a user. Returns whether the client loop should exit and if the
        user has sent their username. Returns it in the form [connected, username_sent]"""
        message_length = int(parts[1])
        message = user_conn.recv(message_length).decode(FORMAT)

        if not username_sent: # assign message to username
            username = self.sanitize_username(message)
            if not username.strip():
                self.handle_disconnect(user_conn, user_addr, username)

            with self.users_lock:
                self.users[user_addr] = username
            self.send_users()
            return True, True

        if message == DISCONNECT_MESSAGE:
            print(f"{username} disconnected.")
            self.handle_disconnect(user_conn, user_addr, username)
            return False, username_sent

        if message == CONNECTIONS_MESSAGE:
            try:
                conn.send(f"There are {len(self.users)} connections.".encode(FORMAT))
            except:
                pass
            return True, username_sent

        if message.startswith(ACCEPT_MESSAGE):
            self.accept_file(conn, message)
            return True, username_sent

        print(f"[{username}] {message}")
        self.broadcast(f"{username}: {message}", user_addr, username)
        return True, username_sent


    def parse_thumb(self, parts: list, conn: SSLSocket, addr: tuple) -> None:
        """Parses through thumbnail data and decides which users to send it to.
        Sends it to all valid users."""
        length = int(parts[1])
        filename = parts[2]
        thumb_data = conn.recv(length)
        with self.clients_lock:
            for addr2, conn2 in self.clients.items():
                if addr2 == addr:
                    continue
                self.send_thumb(conn2, length, filename, thumb_data)


    def parse_file(self, parts: list, conn: SSLSocket, username: str) -> None:
        """Receives file on the server side. Stores the file and determines which
        users to broadcast the file to."""
        file_size: int = int(parts[1])
        file_name = parts[2]

        os.makedirs("server_files", exist_ok=True)
        safe_name = os.path.basename(f"{username}_{file_name}")
        file_path = os.path.join("server_files", safe_name)

        print(f"[RECEIVING FILE] {file_name} ({file_size} bytes) from {username}")

        with open(file_path, "wb") as f:
            bytes_read = 0
            while bytes_read < file_size:
                chunk = conn.recv(min(2048, file_size - bytes_read))
                if not chunk:
                    break
                f.write(chunk)
                bytes_read += len(chunk)

        print(f"[SAVED] {file_path} from {username}: {file_name} ({file_size} bytes)")

        self.pending_files[file_name] = (username, file_path, file_size)
        self.broadcast_file(file_name, username, addr)


if __name__ == "__main__":
    start()