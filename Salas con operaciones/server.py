import socket
import threading
import json
from functools import reduce

salas = {}  # {"sala1": [conn1, conn2]}
lock = threading.Lock()


# ---------------- OPERACIONES (FUNCIONAL) ----------------

def suma(lista):
    return reduce(lambda a, b: a + b, lista)

def multiplicacion(lista):
    return reduce(lambda a, b: a * b, lista)

def filtrar_pares(lista):
    return list(filter(lambda x: x % 2 == 0, lista))

def cuadrados(lista):
    return list(map(lambda x: x ** 2, lista))


def procesar_operacion(operacion, datos):
    if operacion == "suma":
        return suma(datos)

    elif operacion == "multiplicacion":
        return multiplicacion(datos)

    elif operacion == "filtrar_pares":
        return filtrar_pares(datos)

    elif operacion == "cuadrados":
        return cuadrados(datos)

    else:
        return "ERROR: operación no válida"


# ---------------- FUNCIONES DE SALAS ----------------

def enviar_a_sala(sala, mensaje):
    with lock:
        if sala in salas:
            for cliente_conn in salas[sala]:
                try:
                    cliente_conn.send(json.dumps(mensaje).encode("utf-8"))
                except:
                    pass


def manejar_cliente(conn, addr):
    print(f"[NUEVO CLIENTE] {addr}")

    sala_actual = None
    nombre_cliente = None

    try:
        while True:
            data = conn.recv(4096).decode("utf-8")

            if not data:
                break

            paquete = json.loads(data)
            tipo = paquete.get("tipo")

            # ---------------- UNIRSE A SALA ----------------
            if tipo == "unirse":
                nombre_cliente = paquete.get("nombre")
                sala_actual = paquete.get("sala")

                with lock:
                    if sala_actual not in salas:
                        salas[sala_actual] = []
                    salas[sala_actual].append(conn)

                print(f"[INFO] {nombre_cliente} se unió a {sala_actual}")

                conn.send(json.dumps({
                    "tipo": "info",
                    "mensaje": f"Te uniste a la sala {sala_actual}"
                }).encode("utf-8"))

                enviar_a_sala(sala_actual, {
                    "tipo": "info",
                    "mensaje": f"{nombre_cliente} se unió a la sala {sala_actual}"
                })

            # ---------------- MENSAJE NORMAL ----------------
            elif tipo == "mensaje":
                texto = paquete.get("mensaje")

                enviar_a_sala(sala_actual, {
                    "tipo": "mensaje",
                    "nombre": nombre_cliente,
                    "mensaje": texto
                })

            # ---------------- OPERACIÓN ----------------
            elif tipo == "operacion":
                operacion = paquete.get("operacion")
                datos = paquete.get("datos")

                resultado = procesar_operacion(operacion, datos)

                enviar_a_sala(sala_actual, {
                    "tipo": "resultado",
                    "nombre": nombre_cliente,
                    "operacion": operacion,
                    "datos": datos,
                    "resultado": resultado
                })

            # ---------------- SALIR ----------------
            elif tipo == "salir":
                break

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")

    finally:
        with lock:
            if sala_actual in salas and conn in salas[sala_actual]:
                salas[sala_actual].remove(conn)

                if len(salas[sala_actual]) == 0:
                    del salas[sala_actual]

        conn.close()
        print(f"[DESCONECTADO] {addr}")


def iniciar_servidor(host="0.0.0.0", port=5555):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, port))
    servidor.listen()

    print(f"[SERVIDOR ACTIVO] {host}:{port}")

    while True:
        conn, addr = servidor.accept()
        hilo = threading.Thread(target=manejar_cliente, args=(conn, addr))
        hilo.start()

        print(f"[HILOS ACTIVOS] {threading.active_count() - 1}")


if __name__ == "__main__":
    iniciar_servidor()