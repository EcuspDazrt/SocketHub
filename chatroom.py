# SocketHub
# - Secure user to user chatroom experience, featuring text and file sharing, without a limit.

# - Chatroom

import threading
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image
import clientmethod
from customtkinter import CTkButton, CTkFrame

# Chatroom File
# - Made using Python 3.13

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class Chatroom(ctk.CTkToplevel):
    def __init__(self, ip):
        super().__init__()
        self.title("SocketHub Chatroom")
        self.geometry("803x532")
        self.configure(fg_color="#95B3CF")
        self.resizable(False, False)
        self.iconbitmap("resources/logo.ico")
        self.lift()
        self.users = {}
        self.username_sent = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.colors = ["#EBEBEB", "#FFFFFF", "#0078FF", "#4D4D4D", "#0063D2"]

        long_logo = ctk.CTkImage(
            light_image=Image.open("resources/chatroomtitle.png"),
            dark_image=Image.open("resources/chatroomtitle.png"),
            size=(184, 60)
        )

        logo_label = ctk.CTkLabel(self, image=long_logo, text="")

        logo_label.image = long_logo
        logo_label.place(x=0, y=00)

        self.cuserspanel = ctk.CTkScrollableFrame(self, width=179, height=532, fg_color="#B9C3CD")
        self.cuserspanel.place(x=630, y=0)

        self.users_header = ctk.CTkLabel(self.cuserspanel, text="Users:", font=("Roboto", 25, "bold"), text_color="white", fg_color="#B9C3CD")
        self.users_header.pack(fill="x", pady=(10,5))

        self.cusersline = ctk.CTkFrame(self, width=15, height=560, fg_color="#839EB7")
        self.cusersline.place(x=630, y=-20)

        self.chat_frame = ctk.CTkScrollableFrame(self, width=550, height=350, fg_color="#95B3CF")
        self.chat_frame.place(x=30, y=70)

        self.entry = ctk.CTkEntry(self, width=500)
        self.entry.place(x=15, y=485)

        self.entry.bind("<Return>", lambda event: self.send())

        self.send_button = ctk.CTkButton(self, text="Send", command=self.send, width=100)
        self.send_button.place(x=520, y=485)


        self.file_button = ctk.CTkButton(self, text="+", font=("Roboto", 20), command=self.send_file, width=30, height=30)
        self.file_button.place(x=521, y=445)

        self.messages = []

        threading.Thread(target=lambda: clientmethod.start(ip, self.display_message, self.display_users), daemon=True).start()

        self.titlebar = ctk.CTkLabel(self, text=f"Anonymous's Chatroom", font=("Roboto", 25, "bold"), text_color="white")
        self.titlebar.place(x=180, y=10)

    def on_close(self):
        try:
            # Send disconnect message to the server
            clientmethod.send_message("!DISCONNECT")
        except Exception as e:
            print(f"[ERROR] Could not send disconnect: {e}")
        finally:
            # Then destroy the window
            self.destroy()

    def display_message(self, msg):
        self.after(0, lambda: self._display(msg))

    def display_users(self, users, conns):
        if users:
            first_user = next(iter(users.values()))
            self.titlebar.configure(text=f"{first_user}'s Chatroom")

        self.users = users

        for widget in self.cuserspanel.winfo_children()[1:]:
            widget.destroy()

        for user in users.values():
            label = ctk.CTkLabel(self.cuserspanel, text=user, anchor="center", justify="center", text_color="white", fg_color="#9AAFC5", corner_radius=6, width=160, height=25)
            label.pack(fill="x", pady=3, padx=10)

    def _display(self, msg):
        frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        frame.pack(fill="x", pady=(1, 0), anchor="w")

        label = ctk.CTkLabel(frame, text=msg, anchor="w", justify="left", text_color="white", wraplength=480)
        label.pack(fill="x", padx=(5,5), pady=0)

        if "is trying to share" in msg and "Press the button" in msg:
            import re
            match = re.search(r"share\s+(.+?)\s+with you", msg)
            if match:
                filename = match.group(1).strip()

                accept_btn = ctk.CTkButton(frame, text="Accept", width=70, height=25, fg_color="#4CAF50")
                accept_btn.configure(command=lambda f=filename, b=accept_btn: self.accept_file(f, b))
                accept_btn.pack(side="right", padx=(10, 10))

        self.chat_frame._parent_canvas.yview_moveto(1)  # scroll to bottom


    def accept_file(self, filename, button):
        clientmethod.send_message(f"!ACCEPT {filename}")
        button.configure(state="disabled", text="Accepted")

    def send(self):
        msg = self.entry.get().strip()
        if msg.startswith("!FILE"):
            self.send_file()
            return
        if not self.username_sent:
            self.username_sent = True
        else:
            if not msg.startswith("!ACCEPT"):
                self.display_message(f"You: {msg}")  # show your own message immediately
        clientmethod.send_message(msg)
        self.entry.delete(0, "end")

    def send_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            clientmethod.send_file(filepath)


if __name__ == "__main__":
    app = Chatroom(ip="192.168.208.80")
    app.mainloop()
