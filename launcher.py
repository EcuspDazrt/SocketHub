import subprocess
import sys
import os

def real_exe_dir():
    # When frozen, sys.argv[0] gives the real executable path on disk
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        return os.path.dirname(__file__)

launcher_dir = real_exe_dir()
GUI_EXE = os.path.join(launcher_dir, "SocketHub.exe")

print("Running GUI from:", GUI_EXE)

while True:
    proc = subprocess.Popen([GUI_EXE])
    proc.wait()
    print("GUI exited with code:", proc.returncode)
    if proc.returncode == 5:
        continue
    break