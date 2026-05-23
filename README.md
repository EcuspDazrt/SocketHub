# SocketHub

**SocketHub** is a local-network peer-to-peer chat application built with Python. It supports real-time text messaging, file sharing with transfer requests, and image thumbnail previews — all wrapped in a clean GUI built with CustomTkinter.

---

## Features

- **Host or Join**: Launch a server on your machine or connect to one on your local network
- **Real-time Messaging**: Chat instantly with everyone connected to the room
- **File Sharing**: Send files to other users; recipients get a prompt to accept before the transfer begins
- **Image Thumbnails**: Image files display a 150×150 preview inline in the chat
- **Live User List**: A sidebar shows all currently connected users
- **Auto-Restart Support**: The launcher automatically restarts the GUI after the server is stopped and a new session begins

---

## Project Structure

```
SocketHub/
├── app.py            # Main launcher GUI (host or join screen)
├── chatroom.py       # Chatroom window UI and logic
├── clientmethod.py   # Client-side socket handling (send/receive)
├── client.py         # Standalone terminal client (for testing)
├── server.py         # Server logic (connections, broadcasting, file handling)
├── launcher.py       # Entry point wrapper — restarts GUI when hosting ends
├── requirements.txt  # Python dependencies
└── resources/
    ├── logo.ico
    ├── launchertitle.png
    └── chatroomtitle.png
```

---

## Requirements

- Python 3.10+ (uses `match`/`case` syntax)
- Dependencies listed in `requirements.txt`:

```
customtkinter==5.2.2
darkdetect==0.8.0
packaging==26.2
pillow==12.2.0
```

Install them with:

```bash
pip install -r requirements.txt
```

---

## Getting Started

### Running from Source

**To host a server and join the chatroom:**
```bash
python launcher.py
```
Then click **Host a Server** in the launcher window. Your local IP will be used automatically.

**To join an existing server:**
```bash
python app.py
```
Enter the host's local IP address and click **Join a Server**.

### Running the Executable

If you have the compiled `SocketHub.exe`, simply run `launcher.py` (or the compiled launcher) and it will locate and launch the executable automatically.

---

## How It Works

1. **Hosting**: `server.py` binds to port `5051` on the local machine and listens for incoming connections. Each client gets its own thread.
2. **Joining**: `clientmethod.py` connects to the server and starts a background receive thread. Messages, file notifications, thumbnails, and user list updates all arrive over the same socket using a custom header protocol.
3. **File Transfers**: When a user sends a file, the server stores it temporarily and broadcasts a transfer request to other users. Recipients click **Accept** to receive the file, which is saved to a local `downloads/` folder.
4. **Headers**: All messages use a 64-byte fixed-length header formatted as `TYPE|LENGTH|...` to frame data before reading the payload.

---

## Notes

- SocketHub is designed for **local network use only**. The server binds to the machine's LAN IP and is not configured for internet-facing deployment.
- Files sent through the chat are temporarily stored in `server_files/` on the host machine and cleaned up when the sender disconnects.
- Usernames are sanitized to printable ASCII and capped at 20 characters.
- The first user to connect to a session is shown as the chatroom "owner" in the title bar.

---

## License

This project is unlicensed. Feel free to use and modify it for personal or educational purposes.
