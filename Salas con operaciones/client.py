import socket
import threading
import json


def recibir(cliente):
    while True:
        try:
            data = cliente.recv(4096).decode("utf-8")
            if not data:
                break

            mensaje = json.loads(data)

            if mensaje["tipo"] == "mensaje":
                print(f"\n[{mensaje['nombre']}]: {mensaje['mensaje']}")

            elif mensaje["tipo"] == "resultado":
                print(f"\n[RESULTADO] {mensaje['nombre']} pidió {mensaje['operacion']}")
                print(f"Datos: {mensaje['datos']}")
                print(f"Resultado: {mensaje['resultado']}")

            elif mensaje["tipo"] == "info":
                print(f"\n[SERVIDOR]: {mensaje['mensaje']}")

        except:
            break


def main():
    host = "127.0.0.1"
    port = 5555

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((host, port))

    nombre = input("Nombre: ")
    sala = input("Sala: ")

    # unirse
    cliente.send(json.dumps({
        "tipo": "unirse",
        "nombre": nombre,
        "sala": sala
    }).encode("utf-8"))

    hilo = threading.Thread(target=recibir, args=(cliente,))
    hilo.daemon = True
    hilo.start()

    print("\nEscribe mensajes normales o comandos:")
    print("Ejemplo: op suma 1,2,3")
    print("Ejemplo: op multiplicacion 2,3,4")
    print("Ejemplo: op filtrar_pares 1,2,3,4,5")
    print("Ejemplo: op cuadrados 2,3,4")
    print("Escribe 'salir' para desconectarte\n")

    while True:
        texto = input("")

        if texto.lower() == "salir":
            cliente.send(json.dumps({"tipo": "salir"}).encode("utf-8"))
            break

        # si empieza con op -> operación
        if texto.startswith("op "):
            try:
                partes = texto.split(" ", 2)
                operacion = partes[1]
                numeros = list(map(int, partes[2].split(",")))

                cliente.send(json.dumps({
                    "tipo": "operacion",
                    "operacion": operacion,
                    "datos": numeros
                }).encode("utf-8"))

            except:
                print("Formato incorrecto. Ej: op suma 1,2,3")

        else:
            cliente.send(json.dumps({
                "tipo": "mensaje",
                "mensaje": texto
            }).encode("utf-8"))

    cliente.close()
    print("Desconectado.")


if __name__ == "__main__":
    main()