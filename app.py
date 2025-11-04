# SocketHub
# - Secure user to user chatroom experience, featuring text and file sharing, without a limit.

import threading
import customtkinter as ctk
from PIL import Image
import clientmethod
import chatroom
from customtkinter import CTkButton, CTkFrame

# Launcher File
# - Made using Python 3.13

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("SocketHub Client Launcher")
        self.geometry("803x532")
        self.configure(fg_color="#95B3CF")
        self.resizable(False, False)
        self.iconbitmap("resources/logo.ico")

        self.colors = ["#EBEBEB", "#FFFFFF", "#0078FF", "#4D4D4D", "#0063D2"]

        long_logo = ctk.CTkImage(
            light_image=Image.open("resources/launchertitle.png"),
            dark_image=Image.open("resources/launchertitle.png"),
            size=(250, 100)
        )

        logo_label = ctk.CTkLabel(self, image=long_logo, text="")

        logo_label.image = long_logo
        logo_label.place(x=255, y=60)


        self.outlineframe = ctk.CTkFrame(self, width=438, height=230, fg_color=self.colors[0])
        self.outlineframe.place(relx=0.5, y=275, anchor="center")
        self.mainframe = ctk.CTkFrame(self.outlineframe, width=433, height=222, fg_color=self.colors[1])
        self.mainframe.place(relx=0.5, rely=0.5, anchor="center")



        self.hostbutton = ctk.CTkButton(self.mainframe, width=187, height=37, text="Host a Server", font=("Arial", 14, "bold"), fg_color=self.colors[2], text_color=self.colors[1])
        self.hostbutton.place(relx=0.5, y=50, anchor="center")
        self.hostbutton.update_idletasks()

        self.outline(self.hostbutton)


        self.hostdescription = ctk.CTkLabel(self.mainframe, width=175, height=20, text="Host a chatroom on your device", font=("Arial", 11, "normal"), text_color=self.colors[3])
        self.hostdescription.place(relx=0.5, y=80, anchor="center")

        self.ipentry = ctk.CTkEntry(self.mainframe, width=150, height=20, placeholder_text="Enter IP Here")
        self.ipentry.place(relx=0.5, y=185, anchor="center")

        self.joinbutton = ctk.CTkButton(self.mainframe, width=187, height=37, text="Join a Server", font=("Arial", 14, "bold"), fg_color=self.colors[2], text_color=self.colors[1], command=lambda: self.connect(self.ipentry.get()))
        self.joinbutton.place(relx=0.5, y=145, anchor="center")
        self.joinbutton.update_idletasks()

        self.outline(self.joinbutton)

    def connect(self, ip):
        self.withdraw()
        chatroom.Chatroom(ip)


    def outline(self, button):
        if button == self.mainframe:
            outline = ctk.CTkFrame(self, width=button.winfo_width() + 5, height=button.winfo_height() + 5,
                                   fg_color=self.colors[0])
            print("hi")
        else:
            outline = ctk.CTkFrame(self.mainframe,width = button.winfo_width()+5, height = button.winfo_height()+5,
                                   fg_color=self.colors[4])
        outline.place(relx=0.5, y=button.winfo_y()+10, anchor="center")
        button.place_forget()
        if isinstance(button, CTkButton):
            button = CTkButton(outline, width=187, height=37, text=button._text, fg_color=button._fg_color,
                            text_color=self.colors[1], font=("Arial", 14, "bold"))
            button.place(relx=0.5, rely=0.5, anchor="center")
            button.lift()
            if button._text == "Join a Server":
                button.configure(command=lambda: self.connect(self.ipentry.get()))
        else:
            button = CTkFrame(outline, width=433, height=222, fg_color=button._fg_color)
            button.place(relx=0.5, rely=0.5, anchor="center")
            button.lift()
        button.update_idletasks()

if __name__ == "__main__":
    app = App()
    app.mainloop()