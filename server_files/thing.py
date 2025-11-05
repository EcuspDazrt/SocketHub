import pygame
import socket
import threading
import sys

# --- CONFIG ---
WIDTH, HEIGHT = 600, 400
PORT = 5000

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Chat")
font = pygame.font.SysFont(None, 24)

messages = []       # Chat history
input_text = ""     # Current typed text
conn = None         # Connection socket
running = True


def draw_screen():
    screen.fill((30, 30, 30))
    # Draw chat messages
    y = 10
    for msg in messages[-15:]:
        txt = font.render(msg, True, (200, 200, 200))
        screen.blit(txt, (10, y))
        y += 20
    # Draw input box
    pygame.draw.rect(screen, (50, 50, 50), (10, HEIGHT-40, WIDTH-20, 30))
    txt = font.render(input_text, True, (255, 255, 255))
    screen.blit(txt, (15, HEIGHT-35))
    pygame.display.flip()


def listen_thread(sock):
    """Background thread: receive messages."""
    global running
    while running:
        try:
            data = sock.recv(1024)
            if not data:
                break
            messages.append("Them: " + data.decode())
        except:
            break


def host():
    global conn
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(1)
    print("Waiting for connection...")
    conn, addr = server.accept()
    print("Connected:", addr)
    threading.Thread(target=listen_thread, args=(conn,), daemon=True).start()


def join(ip):
    global conn
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((ip, PORT))
    print("Connected to host")
    threading.Thread(target=listen_thread, args=(conn,), daemon=True).start()


mode = input("Host or Join (h/j)? ").strip().lower()
if mode == "h":
    threading.Thread(target=host, daemon=True).start()
elif mode == "j":
    ip = input("Enter host IP: ").strip()
    threading.Thread(target=join, args=(ip,), daemon=True).start()
else:
    print("Invalid choice.")
    sys.exit()


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and conn:
                if input_text.strip():
                    msg = input_text.strip()
                    conn.sendall(msg.encode())
                    messages.append("Me: " + msg)
                input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                if event.unicode.isprintable():
                    input_text += event.unicode

    draw_screen()

pygame.quit()
if conn:
    conn.close()
