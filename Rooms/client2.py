import socket
import threading


class ChatClient:
    def __init__(self, host="192.168.1.3", port=5555):
        self.host = host
        self.port = port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.client_socket.connect((self.host, self.port))

        thread = threading.Thread(target=self.receive_messages)
        thread.daemon = True
        thread.start()

        while True:
            msg = input("> ")

            if msg.strip() == "":
                continue

            self.client_socket.send(msg.encode("utf-8"))

            if msg.lower() == "/quit":
                break

        self.client_socket.close()

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if not message:
                    break
                print(message)
            except:
                break


if __name__ == "__main__":
    client = ChatClient()
    client.start()