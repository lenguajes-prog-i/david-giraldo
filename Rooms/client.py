import socket
import threading
import pickle
import struct


class ChatClient:
    def __init__(self, host="10.127.150.220", port=5555):
        self.host = host
        self.port = port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

    # ENVIAR CON PICKLE
  
    def send_pickle(self, obj):
        try:
            data = pickle.dumps(obj)
            header = struct.pack("!I", len(data))  # 4 bytes con tamaño
            self.client_socket.sendall(header + data)
        except:
            print("[ERROR] No se pudo enviar el mensaje.")
            self.running = False

    
    # RECIBIR CON PICKLE
   
    def recv_all(self, size):
        data = b""
        while len(data) < size:
            packet = self.client_socket.recv(size - len(data))
            if not packet:
                return None
            data += packet
        return data

    def recv_pickle(self):
        try:
            header = self.recv_all(4)
            if not header:
                return None

            msg_len = struct.unpack("!I", header)[0]
            data = self.recv_all(msg_len)

            if not data:
                return None

            return pickle.loads(data)

        except:
            return None

   
    # INICIO CLIENTE
   
    def start(self):
        self.client_socket.connect((self.host, self.port))

        thread = threading.Thread(target=self.receive_messages)
        thread.daemon = True
        thread.start()

        while self.running:
            msg = input("> ")

            if msg.strip() == "":
                continue

            # Enviar como objeto pickle
            self.send_pickle({"message": msg})

            if msg.lower() == "/quit":
                self.running = False
                break

        self.client_socket.close()

   
    # RECIBIR MENSAJES EN HILO
   
    def receive_messages(self):
        while self.running:
            packet = self.recv_pickle()

            if packet is None:
                print("\n[INFO] Conexión cerrada por el servidor.")
                self.running = False
                break

            if "message" in packet:
                print(packet["message"], end="")
            else:
                print("[ERROR] Mensaje recibido mal formado.")


if __name__ == "__main__":
    client = ChatClient()
    client.start()