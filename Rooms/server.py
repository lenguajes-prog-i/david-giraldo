import socket
import threading
import pickle
import struct


class ChatServer:
    def __init__(self, host="10.127.150.102", port=5555):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        # socket -> {"nickname": str, "room": str}
        self.clients = {}

        # nickname -> socket
        self.nicknames = {}

        self.lock = threading.Lock()

    # =======================
    # SERIALIZACIÓN PICKLE
    # =======================

    def send_pickle(self, client_socket, obj):
        try:
            data = pickle.dumps(obj)
            header = struct.pack("!I", len(data))  # tamaño del mensaje (4 bytes)
            client_socket.sendall(header + data)
        except:
            self.disconnect_client(client_socket)

    def recv_pickle(self, client_socket):
        try:
            header = self.recv_all(client_socket, 4)
            if not header:
                return None

            msg_len = struct.unpack("!I", header)[0]
            data = self.recv_all(client_socket, msg_len)
            if not data:
                return None

            return pickle.loads(data)
        except:
            return None

    def recv_all(self, client_socket, size):
        data = b""
        while len(data) < size:
            packet = client_socket.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    # =======================
    # SERVIDOR
    # =======================

    def start(self):
        print(f"[INFO] Servidor iniciado en {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"[+] Conexión entrante desde {addr}")

            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.start()

    def handle_client(self, client_socket):
        try:
            # pedir nickname
            self.send_pickle(client_socket, {"type": "info", "message": "Ingresa tu nickname:"})

            data = self.recv_pickle(client_socket)
            if not data or "message" not in data:
                self.disconnect_client(client_socket)
                return

            nickname = data["message"].strip()
            if not nickname:
                nickname = "Anonimo"

            with self.lock:
                if nickname in self.nicknames:
                    self.send_pickle(client_socket, {"type": "error", "message": "Ese nickname ya está en uso."})
                    self.disconnect_client(client_socket)
                    return

                self.clients[client_socket] = {"nickname": nickname, "room": None}
                self.nicknames[nickname] = client_socket

            self.send_pickle(
                client_socket,
                {"type": "info", "message": "Bienvenido. Usa /join <room> para entrar a una sala.\n"}
            )

            while True:
                packet = self.recv_pickle(client_socket)
                if packet is None:
                    break

                if "message" not in packet:
                    self.send_pickle(client_socket, {"type": "error", "message": "Mensaje inválido."})
                    continue

                message = packet["message"].strip()
                if not message:
                    continue

                if message.startswith("/"):
                    self.process_command(client_socket, message)
                else:
                    self.send_message_to_room(client_socket, message)

        except:
            pass

        self.disconnect_client(client_socket)

    def process_command(self, client_socket, command):
        parts = command.split(" ", 2)
        cmd = parts[0].lower()

        if cmd == "/join":
            if len(parts) < 2:
                self.send_pickle(client_socket, {"type": "error", "message": "Uso: /join <sala>\n"})
                return
            self.join_room(client_socket, parts[1].strip())

        elif cmd == "/leave":
            self.leave_room(client_socket)

        elif cmd == "/rooms":
            self.list_rooms(client_socket)

        elif cmd == "/msg":
            if len(parts) < 2:
                self.send_pickle(client_socket, {"type": "error", "message": "Uso: /msg <mensaje>\n"})
                return
            self.send_message_to_room(client_socket, parts[1])

        # =======================
        # NUEVO COMANDO /pm
        # =======================
        elif cmd == "/pm":
            if len(parts) < 3:
                self.send_pickle(client_socket, {"type": "error", "message": "Uso: /pm <nickname> <mensaje>\n"})
                return

            target_nick = parts[1].strip()
            msg = parts[2].strip()

            if not target_nick or not msg:
                self.send_pickle(client_socket, {"type": "error", "message": "Uso: /pm <nickname> <mensaje>\n"})
                return

            self.private_message(client_socket, target_nick, msg)

        elif cmd == "/quit":
            self.send_pickle(client_socket, {"type": "info", "message": "Desconectando...\n"})
            self.disconnect_client(client_socket)

        else:
            self.send_pickle(client_socket, {"type": "error", "message": "Comando desconocido.\n"})

    # =======================
    # SALAS
    # =======================

    def join_room(self, client_socket, room):
        with self.lock:
            current_room = self.clients[client_socket]["room"]

            if current_room is not None:
                self.send_pickle(client_socket, {"type": "error", "message": "Error: Ya estás en una sala. Usa /leave.\n"})
                return

            self.clients[client_socket]["room"] = room
            nickname = self.clients[client_socket]["nickname"]

        print(f"[+] {nickname} se unió a sala '{room}'")

        self.send_pickle(client_socket, {"type": "info", "message": f"Te uniste a la sala '{room}'\n"})
        self.broadcast(room, {"type": "info", "message": f"[INFO] {nickname} entró a la sala.\n"}, exclude=client_socket)

    def leave_room(self, client_socket):
        with self.lock:
            room = self.clients[client_socket]["room"]

            if room is None:
                self.send_pickle(client_socket, {"type": "error", "message": "No estás en ninguna sala.\n"})
                return

            self.clients[client_socket]["room"] = None
            nickname = self.clients[client_socket]["nickname"]

        print(f"[-] {nickname} salió de sala '{room}'")

        self.send_pickle(client_socket, {"type": "info", "message": "Saliste de la sala.\n"})
        self.broadcast(room, {"type": "info", "message": f"[INFO] {nickname} salió de la sala.\n"}, exclude=client_socket)

    def list_rooms(self, client_socket):
        rooms = set()

        with self.lock:
            for info in self.clients.values():
                if info["room"]:
                    rooms.add(info["room"])

        if not rooms:
            self.send_pickle(client_socket, {"type": "info", "message": "No hay salas activas.\n"})
        else:
            room_list = "\n".join(rooms)
            self.send_pickle(client_socket, {"type": "info", "message": f"Salas disponibles:\n{room_list}\n"})

    def send_message_to_room(self, client_socket, message):
        with self.lock:
            room = self.clients[client_socket]["room"]
            nickname = self.clients[client_socket]["nickname"]

        if room is None:
            self.send_pickle(client_socket, {"type": "error", "message": "Error: No estás en una sala. Usa /join <sala>\n"})
            return

        formatted = f"{nickname}: {message}\n"
        print(f"[{room}] {formatted.strip()}")

        self.broadcast(room, {"type": "room", "message": formatted}, exclude=None)

    def broadcast(self, room, obj, exclude=None):
        with self.lock:
            clients_copy = list(self.clients.items())

        for client, info in clients_copy:
            if info["room"] == room and client != exclude:
                self.send_pickle(client, obj)

    # =======================
    # MENSAJES PRIVADOS
    # =======================

    def private_message(self, sender_socket, target_nick, message):
        with self.lock:
            sender_nick = self.clients[sender_socket]["nickname"]

            if target_nick not in self.nicknames:
                self.send_pickle(sender_socket, {"type": "error", "message": f"Error: El usuario '{target_nick}' no existe.\n"})
                return

            target_socket = self.nicknames[target_nick]

        try:
            # mensaje al destino
            self.send_pickle(target_socket, {
                "type": "pm",
                "from": sender_nick,
                "message": f"[PM de {sender_nick}] {message}\n"
            })

            # confirmación al remitente
            self.send_pickle(sender_socket, {
                "type": "pm",
                "from": "Servidor",
                "message": f"[PM enviado a {target_nick}] {message}\n"
            })

        except:
            self.send_pickle(sender_socket, {"type": "error", "message": f"Error: El usuario '{target_nick}' está desconectado.\n"})
            self.disconnect_client(target_socket)

    # =======================
    # DESCONEXIÓN
    # =======================

    def disconnect_client(self, client_socket):
        with self.lock:
            if client_socket not in self.clients:
                return

            nickname = self.clients[client_socket]["nickname"]
            room = self.clients[client_socket]["room"]

            del self.clients[client_socket]

            if nickname in self.nicknames:
                del self.nicknames[nickname]

        print(f"[-] {nickname} desconectado")

        if room:
            self.broadcast(room, {"type": "info", "message": f"[INFO] {nickname} se desconectó.\n"}, exclude=None)

        try:
            client_socket.close()
        except:
            pass


if __name__ == "__main__":
    server = ChatServer()
    server.start()