import socket
import threading
import json
import tkinter as tk
from tkinter import ttk
import sys
import time

HOST = "127.0.0.1"
PORT = 5001


# сервер
clients = []
positions = {}  # {"user": (x, y)}


def broadcast(data, exclude=None):
    """Розсилає JSON-повідомлення всім клієнтам."""
    msg = json.dumps(data).encode()
    for c in clients:
        if c is not exclude:
            try:
                c.sendall(msg + b"\n")
            except:
                pass


def handle_client(conn, addr):
    """Логіка обробки одного клієнта."""
    print(f"[NEW] {addr} connected")
    clients.append(conn)

    username = None

    try:
        for line in conn.makefile("r"):
            data = json.loads(line.strip())

            if data["type"] == "join":
                username = data["user"]
                positions[username] = (0, 0)
                print(f"[JOIN] {username}")
                broadcast({"type": "info", "text": f"{username} приєднався."})

            elif data["type"] == "position":
                positions[data["user"]] = (data["x"], data["y"])
                broadcast({"type": "positions", "positions": positions})

            elif data["type"] == "message":
                broadcast(data)

    except Exception as e:
        print("ERROR:", e)

    finally:
        if username:
            if username in positions:
                del positions[username]
            broadcast({"type": "info", "text": f"{username} відключився."})

        conn.close()
        clients.remove(conn)
        print(f"[QUIT] {addr} disconnected")


def run_server():
    """Запуск сервера."""
    print(f"SERVER RUNNING ON {HOST}:{PORT}")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind((HOST, PORT))
    srv.listen()

    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


# клієнт
class ClientApp:
    def __init__(self, username):
        self.username = username
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))

        self.send({"type": "join", "user": username})

        # ------------------ GUI ------------------
        self.root = tk.Tk()
        self.root.title(f"Клієнт: {username}")

        self.canvas = tk.Canvas(self.root, width=400, height=400, bg="white")
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        right = ttk.Frame(self.root)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.chat = tk.Text(right, state="disabled", width=40, height=20)
        self.chat.pack()

        self.entry = ttk.Entry(right)
        self.entry.pack(fill=tk.X)
        self.entry.bind("<Return>", self.on_enter)

        self.positions = {}

        # запускаємо потік слухача
        threading.Thread(target=self.listen, daemon=True).start()

        self.root.mainloop()

    def send(self, data):
        msg = json.dumps(data).encode()
        self.sock.sendall(msg + b"\n")

    def listen(self):
        for line in self.sock.makefile("r"):
            data = json.loads(line.strip())
            self.handle_event(data)

    def handle_event(self, data):
        if data["type"] == "positions":
            self.positions = data["positions"]
            self.draw_positions()

        elif data["type"] == "message":
            self.write_chat(f"{data['user']}: {data['text']}")

        elif data["type"] == "info":
            self.write_chat(f"* {data['text']}")

    def draw_positions(self):
        self.canvas.delete("all")
        for user, (x, y) in self.positions.items():
            px = x * 4
            py = y * 4
            self.canvas.create_oval(px-6, py-6, px+6, py+6, fill="red")
            self.canvas.create_text(px, py-12, text=user)

    def write_chat(self, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", text + "\n")
        self.chat.configure(state="disabled")
        self.chat.yview("end")

    def on_enter(self, event):
        text = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        if text.startswith("/move"):
            try:
                _, x, y = text.split()
                self.send({
                    "type": "position",
                    "user": self.username,
                    "x": float(x),
                    "y": float(y),
                })
            except:
                self.write_chat("Невірний формат. Використовуй: /move X Y")
        else:
            self.send({
                "type": "message",
                "user": self.username,
                "text": text
            })


#вхід
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Використання:")
        print("  python app.py server")
        print("  python app.py client")
        sys.exit()

    mode = sys.argv[1]

    if mode == "server":
        run_server()

    elif mode == "client":
        name = input("Введіть ім'я: ")
        ClientApp(name)

    else:
        print("Невідомий режим. Використай: server або client.")