import socket
import json


def main():
    host = "127.0.0.1"
    port = 5555

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((host, port))

    tarea = {
        "cliente": "Cliente 7",
        "operacion": "cuadrados",
        "datos": [3, 5, 7, 9]
    }

    cliente.send(json.dumps(tarea).encode("utf-8"))

    respuesta = cliente.recv(4096).decode("utf-8")
    print("[RESPUESTA]")
    print(json.loads(respuesta))

    


if __name__ == "__main__":
    main()