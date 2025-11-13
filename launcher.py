# SocketHub
# - Secure user to user chatroom experience, featuring text and file sharing, without a limit.

# launcher.py - Use this to launch the program.d

import os
import sys
import subprocess

APP = os.path.abspath("app.py")

while True:
    exit_code = subprocess.call([sys.executable, APP])

    if exit_code == 5:
        continue

    break

