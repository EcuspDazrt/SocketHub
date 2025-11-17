# SocketHub
# - Secure user to user chatroom experience, featuring text and file sharing, without a limit.
import socket
import threading
import customtkinter as ctk
from PIL import Image
import server
from customtkinter import CTkButton, CTkFrame
import sys, os

# Launcher File
# - Made using Python 3.13

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
        self.is_hosting = False
        self.title("SocketHub Client Launcher")
        self.geometry("803x532")
        self.configure(fg_color="#95B3CF")
        self.resizable(False, False)
        self.iconbitmap(resource_path("resources/logo.ico"))

        self.colors = ["#EBEBEB", "#FFFFFF", "#0078FF", "#4D4D4D", "#0063D2"]

        long_logo = ctk.CTkImage(
            light_image=Image.open(resource_path("resources/launchertitle.png")),
            dark_image=Image.open(resource_path("resources/launchertitle.png")),
            size=(250, 100)
        )

        logo_label = ctk.CTkLabel(self, image=long_logo, text="")

        logo_label.image = long_logo
        logo_label.place(x=255, y=60)


        self.outlineframe = ctk.CTkFrame(self, width=438, height=230, fg_color=self.colors[0])
        self.outlineframe.place(relx=0.5, y=275, anchor="center")
        self.mainframe = ctk.CTkFrame(self.outlineframe, width=433, height=222, fg_color=self.colors[1])
        self.mainframe.place(relx=0.5, rely=0.5, anchor="center")



        self.hostbutton = ctk.CTkButton(self.mainframe, width=187, height=37, text="Host a Server", font=("Arial", 14, "bold"), fg_color=self.colors[2], text_color=self.colors[1], command=lambda: self.start_server())
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

        self.ipentry.bind("<Return>", lambda event: self.connect(self.ipentry.get()))

    def connect(self, ip):
        import chatroom
        self.withdraw()
        chatroom.Chatroom(self, ip, is_host=False)

    def start_server(self):
        self.is_hosting = True
        threading.Thread(target=server.start, daemon=True).start()
        ip = socket.gethostbyname(socket.gethostname())
        import chatroom
        self.withdraw()
        chatroom.Chatroom(self, ip, is_host=True)

    def on_host_exit(self):
        self.is_hosting = True
        self.destroy()

    def close_chatroom(self):
        App.instance.on_host_exit()

    def outline(self, button):
        if button == self.mainframe:
            outline = ctk.CTkFrame(self, width=button.winfo_width() + 5, height=button.winfo_height() + 5,
                                   fg_color=self.colors[0])
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
            elif button._text == "Host a Server":
                button.configure(command=self.start_server)
        else:
            button = CTkFrame(outline, width=433, height=222, fg_color=button._fg_color)
            button.place(relx=0.5, rely=0.5, anchor="center")
            button.lift()
        button.update_idletasks()

if __name__ == "__main__":
    import sys
    sys.exit(main())