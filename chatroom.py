# SocketHub
# - Secure user to user chatroom experience, featuring text and file sharing, without a limit.

# - Chatroom

import threading
import customtkinter as ctk
from PIL import Image
import clientmethod
from customtkinter import CTkButton, CTkFrame

# Chatroom File
# - Made using Python 3.13

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class Chatroom(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("SocketHub Chatroom")
        self.geometry("803x532")
        self.configure(fg_color="#95B3CF")
        self.resizable(False, False)
        self.iconbitmap("resources/logo.ico")
        self.lift()

        self.colors = ["#EBEBEB", "#FFFFFF", "#0078FF", "#4D4D4D", "#0063D2"]

        long_logo = ctk.CTkImage(
            light_image=Image.open("resources/chatroomtitle.png"),
            dark_image=Image.open("resources/chatroomtitle.png"),
            size=(184, 60)
        )

        logo_label = ctk.CTkLabel(self, image=long_logo, text="")

        logo_label.image = long_logo
        logo_label.place(x=0, y=00)

        self.cuserspanel = ctk.CTkFrame(self, width=179, height=532, fg_color="#B9C3CD")
        self.cuserspanel.place(x=630, y=0)

        self.cusersline = ctk.CTkFrame(self, width=15, height=560, fg_color="#839EB7")
        self.cusersline.place(x=630, y=-20)

        ip = clientmethod.getip()

        self.titlebar = ctk.CTkLabel(self, text=f"{ip}'s Chatroom", font=("Roboto", 25, "bold"), text_color="white")
        self.titlebar.place(x=180, y=10)

if __name__ == "__main__":
    app = Chatroom()
    app.mainloop()
