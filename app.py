# SocketHub
# - Secure user to user chatroom experience, featuring text and file sharing, without a limit.
import server
import socket, threading, sys, os
import customtkinter as ctk
import theme as t
from PIL import Image
from customtkinter import CTkButton, CTkFrame

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

def resource_path(path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.dirname(__file__), path)

def main():
    app_instance = App()
    app_instance.mainloop()

    if getattr(app_instance, "is_hosting", False):
        return 5
    return 0


class App(ctk.CTk):
    instance = None

    def __init__(self):
        App.instance = self
        super().__init__()
        self.local_server = None
        self.is_hosting = False
        self.title("SocketHub Client Launcher")
        self.geometry("803x532")
        self.configure(fg_color=t.BG)
        self.resizable(False, False)
        self.iconbitmap(resource_path("resources/logo.ico"))
        self.username = None

        long_logo = ctk.CTkImage(
            light_image=Image.open(resource_path("resources/launchertitle.png")),
            dark_image=Image.open(resource_path("resources/launchertitle.png")),
            size=(250, 100)
        )

        logo_label = ctk.CTkLabel(self, image=long_logo, text="")

        logo_label.image = long_logo
        logo_label.place(x=255, y=60)

        self.outline_frame = ctk.CTkFrame(self, width=438, height=230, fg_color=t.CARD)
        self.outline_frame.place(relx=0.5, y=275, anchor="center")
        self.main_frame = ctk.CTkFrame(self.outline_frame, width=433, height=222, fg_color=t.WHITE)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.host_button = ctk.CTkButton(self.main_frame, width=187, height=37,
                                         text="Host a Server", font=("Arial", 14, "bold"),
                                         fg_color=t.ACCENT, text_color=t.WHITE,
                                         border_width=3, border_color=t.ACCENT_DARK,
                                         command=self.start_server)
        self.host_button.place(relx=0.5, y=50, anchor="center")

        self.host_description = ctk.CTkLabel(self.main_frame, width=175, height=20, text="Host a chatroom on your device", font=("Arial", 11, "normal"), text_color=t.MUTED)
        self.host_description.place(relx=0.5, y=80, anchor="center")

        self.search_button = ctk.CTkButton(self.main_frame, width=187, height=37,
                                           text="Search For a Server", font=("Arial", 14, "bold"),
                                           fg_color=t.ACCENT, text_color=t.WHITE,
                                           border_width=3, border_color=t.ACCENT_DARK,
                                           command=self.search)
        self.search_button.place(relx=0.5, y=145, anchor="center")

        self.username_entry = ctk.CTkEntry(self.main_frame, width=187, placeholder_text="Your name (max 20)")
        self.username_entry.place(relx=0.5, y=185, anchor="center")
        self._entry_border = self.username_entry.cget("border_color")


    def search(self) -> None:
        """Function called by the search button for the user to be able to enter the
        room searching part of the widget. Exits the app widget itself."""
        from server_search import ServerSearch
        if not self.get_username(): return
        self.withdraw()
        ServerSearch(self)


    def start_server(self) -> None:
        """If the user wants to be a host, it spins up a server and navigates them into their own chatroom."""
        from chatroom import Chatroom
        username = self.get_username()
        if not username: return
        self.is_hosting = True
        self.local_server = server.Server()
        threading.Thread(target=self.local_server.start, daemon=True).start()
        threading.Thread(target=self.local_server.run_responder, daemon=True).start()
        ip = socket.gethostbyname(socket.gethostname())
        self.withdraw()
        Chatroom(self, ip, username, is_host=True)


    def on_host_exit(self) -> None:
        """Specifies what happens when the host closes out of their window. Destroys the widget."""
        self.is_hosting = True
        self.destroy()

    @staticmethod
    def close_chatroom() -> None:
        """Calls the chatroom exit function of the app instance."""
        App.instance.on_host_exit()


    def get_username(self) -> str:
        """Retrieves the username from the username entry field."""
        name = self.username_entry.get().strip()[:20]
        if not name or not (name.isascii() and name.isprintable()):
            self.username_entry.configure(border_color=t.FAIL)
            self.username_entry.focus()
            return None
        self.username_entry.configure(border_color=self._entry_border)
        self.username = name
        return name


if __name__ == "__main__":
    sys.exit(main())