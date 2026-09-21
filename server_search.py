import sys, os, json, socket, threading
import customtkinter as ctk
import theme as t
from chatroom import Chatroom
from PIL import Image

def resource_path(path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.dirname(__file__), path)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
DISCOVERY_PORT = 5052

class ServerSearch(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("SocketHub Search")
        self.geometry("803x532")
        self.configure(fg_color="#95B3CF")
        self.resizable(False, False)
        self.iconbitmap(resource_path("resources/logo.ico"))
        self.lift()
        self.rooms = {}

        long_logo = ctk.CTkImage(
            light_image=Image.open(resource_path("resources/chatroomtitle.png")),
            dark_image=Image.open(resource_path("resources/chatroomtitle.png")),
            size=(184, 60)
        )

        logo_label = ctk.CTkLabel(self, image=long_logo, text="")

        logo_label.image = long_logo
        logo_label.place(x=0, y=00)

        self.titlebar = ctk.CTkLabel(self, text=f"Search For A Room", font=("Roboto", 25, "bold"), text_color="white")
        self.titlebar.place(x=180, y=10)

        self.room_frame = ctk.CTkScrollableFrame(self, width=550, height=350, fg_color="#95B3CF")
        self.room_frame.place(x=30, y=70)

        self.start_scan()
        self.display_rooms()
        self.protocol("WM_DELETE_WINDOW", self.on_close)


    def on_close(self):
        self.parent.deiconify()
        self.destroy()

    def start_scan(self):
        threading.Thread(target=self._scan_worker, daemon=True).start()


    def _scan_worker(self):
        self.scan()
        self.after(0, self.display_rooms)


    def scan(self, timeout=1.5):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(timeout)
        s.sendto(b"SOCKETHUB?", ("255.255.255.255", DISCOVERY_PORT))
        rooms = {}
        try:
            while True:
                data, (ip, _) = s.recvfrom(1024)
                rooms[ip] = json.loads(data)
        except socket.timeout:
            self.rooms = rooms
        finally:
            s.close()


    def join(self, ip):
        self.withdraw()
        Chatroom(self, ip, self.parent.username)


    def display_rooms(self):
        for ip, data in self.rooms.items():
            frame = ctk.CTkFrame(self.room_frame, fg_color="transparent")
            frame.pack(fill="x", pady=(1, 0), anchor="w")

            button = ctk.CTkButton(frame, text=data.get('name', 'Anonymous'), anchor="w", text_color="white", command=lambda ip=ip: self.join(ip))
            button.pack(fill="x", padx=(5, 5), pady=0)
