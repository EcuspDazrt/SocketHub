# SocketHub
# - Secure user to user chatroom experience, featuring text and file sharing, without a limit.

# launcher.py - Use this to launch the program.d

import os
import sys
import subprocess

APP = os.path.abspath("app.py")
REQUIREMENTS = [
    "customtkinter",
    "Pillow",
]

def install_missing():
    for package in REQUIREMENTS:
        try:
            __import__(package)
        except ImportError:
            print(f"[INSTALL] Installing missing package: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def run_app():
    return subprocess.call([sys.executable, APP])

if __name__ == "__main__":
    install_missing()

    while True:
        exit_code = run_app()

        if exit_code == 5:
            continue  # restart

        break
