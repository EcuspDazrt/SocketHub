# SocketHub
# - Secure user to user chatroom experience, featuring text and file sharing, without a limit.

# - Chatroom

import threading, time, sys, os, re, subprocess
import customtkinter as ctk
import theme as t
import client
from tkinter import filedialog
from PIL import Image


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

def resource_path(path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.dirname(__file__), path)

class Chatroom(ctk.CTkToplevel):
    def __init__(self, parent, ip, username, is_host=False):
        super().__init__(parent)
        self.is_host = is_host
        self.parent = parent
        self.title("SocketHub Chatroom")
        self.geometry("803x532")
        self.configure(fg_color=t.BG)
        self.resizable(False, False)
        self.iconbitmap(resource_path("resources/logo.ico"))
        self.lift()
        self.users = {}
        self.username = username
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        long_logo = ctk.CTkImage(
            light_image=Image.open(resource_path("resources/chatroomtitle.png")),
            dark_image=Image.open(resource_path("resources/chatroomtitle.png")),
            size=(184, 60)
        )

        logo_label = ctk.CTkLabel(self, image=long_logo, text="")

        logo_label.image = long_logo
        logo_label.place(x=0, y=00)

        self.users_panel = ctk.CTkScrollableFrame(self, width=179, height=532, fg_color=t.PANEL)
        self.users_panel.place(x=630, y=0)

        self.users_header = ctk.CTkLabel(self.users_panel, text="Users:", font=("Roboto", 25, "bold"), text_color="white", fg_color=t.PANEL)
        self.users_header.pack(fill="x", pady=(10,5))

        self.users_line = ctk.CTkFrame(self, width=15, height=560, fg_color=t.PANEL_LINE)
        self.users_line.place(x=630, y=-20)

        self.chat_frame = ctk.CTkScrollableFrame(self, width=550, height=350, fg_color=t.BG)
        self.chat_frame.place(x=30, y=70)

        self.entry = ctk.CTkEntry(self, width=500)
        self.entry.place(x=15, y=485)

        self.entry.bind("<Return>", lambda event: self.send())

        self.send_button = ctk.CTkButton(self, text="Send", command=self.send, width=100)
        self.send_button.place(x=520, y=485)

        self.file_button = ctk.CTkButton(self, text="+", font=("Roboto", 20), command=self.send_file, width=30, height=30)
        self.file_button.place(x=521, y=445)

        self._set_input(False)

        self.messages = []
        self.client = client.Client()

        self.titlebar = ctk.CTkLabel(self, text=f"Anonymous's Chatroom", font=("Roboto", 25, "bold"), text_color="white")
        self.titlebar.place(x=180, y=10)

        threading.Thread(target=lambda: self.client.start(ip, self.display_message, self.display_users), daemon=True).start()

    def on_close(self) -> None:
        """Function that specifies what happens when the user closes the window.
        Destroys the chatroom widget, disconnects the client from the server, and stops the server
        if they are a host."""
        try:
            # Send disconnect message to the server
            self.client.send_message("!DISCONNECT")
        except Exception as e:
            print(f"[ERROR] Could not send disconnect: {e}")
        finally:
            # Then destroy the window
            self.destroy()
            if self.is_host:
                try:
                    from app import App
                    self.parent.local_server.stop()
                    time.sleep(0.2)
                except Exception as e:
                    print("[ERROR STOPPING SERVER]", e)
            try:
                if self.parent is not None:
                    self.parent.deiconify()
            except Exception as e:
                print(f"[ERROR] Could not deiconify the chatroom: {e}")
            if self.is_host:
                sys.exit(5)


    def display_message(self, msg: str) -> None:
        """Helper function meant to display a message to the room."""
        self.after(0, lambda: self._handle(msg))


    def _handle(self, msg: str) -> None:
        """Intermediate function used to filter messages displayed to the user. If it passes
        all the guards, it calls the function that actually displays the message."""
        if msg == "[CONNECTED]":
            self._set_input(True)
            self.client.send_message(self.username)  # first message is the username
            return
        if msg.startswith("[ERROR] Could not connect"):
            print(msg)  # keep the raw error for debugging
            msg = "Couldn't reach that room. Close this window to go back."
        elif msg.startswith("[DISCONNECTED]"):
            print(msg)
            self._set_input(False)
            msg = "Connection lost. Close this window to go back."
        self._display(msg)


    def _set_input(self, enabled: bool) -> None:
        """Sets the state of the chatroom as enabled or disabled so users can't try to send
        a message before they are supposed to be able to."""
        state = "normal" if enabled else "disabled"
        for w in (self.entry, self.send_button, self.file_button):
            w.configure(state=state)
        if enabled:
            self.entry.focus()


    def display_users(self, users: dict) -> None:
        """Helper function meant to update the users column in the chatroom (and slightly delay it)."""
        self.after(0, lambda: self._update_users(users))


    def _update_users(self, users: dict) -> None:
        """Function that actually updates the 'users' column in the state of the widget. Configures the
        name of the host as well."""
        if users:
            first_user = next(iter(users.values()))
            self.titlebar.configure(text=f"{first_user}'s Chatroom")

        self.users = users

        for widget in self.users_panel.winfo_children()[1:]:
            if widget.winfo_exists():
                widget.destroy()

        for user in users.values():
            label = ctk.CTkLabel(self.users_panel, text=user, anchor="center", justify="center", text_color="white", fg_color=t.CHIP, corner_radius=6, width=160, height=25)
            label.pack(fill="x", pady=3, padx=10)


    def _display(self, msg: str, own: bool=False) -> None:
        """Displays the message to the chatroom. Processes thumbnails so compression works properly,
        handles file transfer prompting, and scrolls the user down to the bottom if they are near already."""
        stick = own or self._at_bottom()
        if msg.startswith("[THUMBNAIL]"):
            try:
                parts = msg.replace("[THUMBNAIL] ", "").split("|")
                filename, thumb_path = parts[0], parts[1]
                frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
                frame.pack(fill="x", pady=(1, 0), anchor="w")

                img = Image.open(thumb_path)
                w, h = img.size
                scale = min(1.0, 120 / max(w, h))
                ctk_img = ctk.CTkImage(light_image=img, size=(max(1, int(w * scale)), max(1, int(h * scale))))
                img_label = ctk.CTkLabel(frame, image=ctk_img, text="")
                img_label.image = ctk_img
                img_label.pack(anchor="w", padx=5, pady=(3, 3))
            except Exception as e:
                print(f"[ERROR showing thumbnail] {e}")
            return
        if self.chat_frame:
            frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
            frame.pack(fill="x", pady=(1, 0), anchor="w")

            if frame:
                label = ctk.CTkLabel(
                    frame, text=msg, wraplength=480, text_color=t.TEXT,
                    anchor="e" if own else "w", justify="right" if own else "left",
                    fg_color=t.OWN_BUBBLE if own else "transparent", corner_radius=8,
                )
                label.pack(anchor="e" if own else "w", padx=5)

                if "is trying to share" in msg and "Press the button" in msg:
                    match = re.search(r"share\s+(.+?)\s+with you", msg)
                    if match:
                        filename = match.group(1).strip()

                        accept_btn = ctk.CTkButton(frame, text="Accept", width=70, height=25, fg_color=t.SUCCESS)
                        accept_btn.configure(command=lambda f=filename, b=accept_btn: self.accept_file(f, b))
                        accept_btn.pack(side="right", padx=(10, 10))

            if stick: self._scroll_down()


    def _at_bottom(self) -> bool:
        """Returns whether the user is at the bottom of the scroll view."""
        return self.chat_frame._parent_canvas.yview()[1] >= 0.99


    def _scroll_down(self) -> None:
        """Scrolls the user down to the very bottom of the scroll view."""
        self.chat_frame.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1)


    def accept_file(self, filename: str, button: ctk.CTkButton) -> None:
        """Sends an acceptance message to the server when the user
        accepts a file transfer from another user."""
        self.client.send_message(f"!ACCEPT {filename}")
        button.configure(state="disabled", text="Accepted")


    def send(self) -> None:
        """Universal send function. Manages what sub-send function the message/file goes through
        and sanitizes its input."""
        msg = self.entry.get().strip()
        if msg.startswith("!FILE"):
            self.send_file()
            return
        else:
            if not msg.startswith("!ACCEPT"):
                self._display(msg, own=True)  # show your own message immediately
        self.client.send_message(msg)
        self.entry.focus()


    def send_file(self) -> None:
        """Asks for the file and uses the client send file to send it over to the server."""
        filepath = filedialog.askopenfilename()
        if filepath:
            self.client.send_file(filepath)