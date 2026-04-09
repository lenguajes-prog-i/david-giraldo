import socket
import threading


class ChatServer:
    def __init__(self, host="192.168.1.3", port=5555):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        self.clients = {}  # socket -> {"nickname": str, "room": str}

        self.lock = threading.Lock()

    def start(self):
        print(f"[INFO] Servidor iniciado en {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"[+] Conexión entrante desde {addr}")

            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.start()

    def handle_client(self, client_socket):
        try:
            client_socket.send("Ingresa tu nickname: ".encode("utf-8"))
            nickname = client_socket.recv(1024).decode("utf-8").strip()

            if not nickname:
                nickname = "Anonimo"

            with self.lock:
                self.clients[client_socket] = {"nickname": nickname, "room": None}

            client_socket.send(
                "Bienvenido al servidor. Usa /join <room> para entrar a una sala.\n".encode("utf-8")
            )

            while True:
                message = client_socket.recv(1024).decode("utf-8").strip()

                if not message:
                    break

                if message.startswith("/"):
                    self.process_command(client_socket, message)
                else:
                    self.send_message_to_room(client_socket, message)

        except:
            pass

        self.disconnect_client(client_socket)

    def process_command(self, client_socket, command):
        parts = command.split(" ", 1)
        cmd = parts[0].lower()

        if cmd == "/join":
            if len(parts) < 2:
                client_socket.send("Uso: /join <sala>\n".encode("utf-8"))
                return

            room = parts[1].strip()
            self.join_room(client_socket, room)

        elif cmd == "/leave":
            self.leave_room(client_socket)

        elif cmd == "/rooms":
            self.list_rooms(client_socket)

        elif cmd == "/msg":
            if len(parts) < 2:
                client_socket.send("Uso: /msg <mensaje>\n".encode("utf-8"))
                return
            self.send_message_to_room(client_socket, parts[1])

        elif cmd == "/quit":
            client_socket.send("Desconectando...\n".encode("utf-8"))
            self.disconnect_client(client_socket)

        else:
            client_socket.send("Comando desconocido.\n".encode("utf-8"))

    def join_room(self, client_socket, room):
        with self.lock:
            current_room = self.clients[client_socket]["room"]

            if current_room is not None:
                client_socket.send("Error: Ya estás en una sala. Usa /leave primero.\n".encode("utf-8"))
                return

            self.clients[client_socket]["room"] = room

        nickname = self.clients[client_socket]["nickname"]
        print(f"[+] {nickname} se unió a sala '{room}'")

        client_socket.send(f"Te uniste a la sala '{room}'\n".encode("utf-8"))

        self.broadcast(room, f"[INFO] {nickname} entró a la sala.\n", exclude=client_socket)

    def leave_room(self, client_socket):
        with self.lock:
            room = self.clients[client_socket]["room"]

            if room is None:
                client_socket.send("No estás en ninguna sala.\n".encode("utf-8"))
                return

            self.clients[client_socket]["room"] = None

        nickname = self.clients[client_socket]["nickname"]
        print(f"[-] {nickname} salió de sala '{room}'")

        client_socket.send("Saliste de la sala.\n".encode("utf-8"))
        self.broadcast(room, f"[INFO] {nickname} salió de la sala.\n", exclude=client_socket)

    def list_rooms(self, client_socket):
        rooms = set()

        with self.lock:
            for info in self.clients.values():
                if info["room"]:
                    rooms.add(info["room"])

        if not rooms:
            client_socket.send("No hay salas activas.\n".encode("utf-8"))
        else:
            room_list = "\n".join(rooms)
            client_socket.send(f"Salas disponibles:\n{room_list}\n".encode("utf-8"))

    def send_message_to_room(self, client_socket, message):
        with self.lock:
            room = self.clients[client_socket]["room"]
            nickname = self.clients[client_socket]["nickname"]

        if room is None:
            client_socket.send("Error: No estás en una sala. Usa /join <sala>\n".encode("utf-8"))
            return

        formatted = f"{nickname}: {message}\n"
        print(f"[{room}] {formatted.strip()}")

        self.broadcast(room, formatted, exclude=None)

    def broadcast(self, room, message, exclude=None):
        with self.lock:
            for client, info in self.clients.items():
                if info["room"] == room and client != exclude:
                    try:
                        client.send(message.encode("utf-8"))
                    except:
                        pass

    def disconnect_client(self, client_socket):
        with self.lock:
            if client_socket not in self.clients:
                return

            nickname = self.clients[client_socket]["nickname"]
            room = self.clients[client_socket]["room"]

            del self.clients[client_socket]

        print(f"[-] {nickname} desconectado")

        if room:
            self.broadcast(room, f"[INFO] {nickname} se desconectó.\n", exclude=None)

        try:
            client_socket.close()
        except:
            pass


if __name__ == "__main__":
    server = ChatServer()
    server.start()