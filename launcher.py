import subprocess
import sys
import os

if getattr(sys, "frozen", False):
    launcher_dir = os.path.dirname(sys.executable)  # path to the frozen launcher EXE
else:
    launcher_dir = os.path.dirname(__file__)       # path to .py script

GUI_EXE = os.path.join(launcher_dir, "SocketHubGUI.exe")
print("Running GUI from:", GUI_EXE)  # debug

while True:
    proc = subprocess.Popen([GUI_EXE])
    proc.wait()
    print("GUI exited with code:", proc.returncode)
    if proc.returncode == 5:
        continue
    break