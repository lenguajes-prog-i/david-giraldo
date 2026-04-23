import socket
import threading
import json
from functools import reduce


# ---------------- FUNCIONES (PROGRAMACIÓN FUNCIONAL) ----------------

def suma(lista):
    return reduce(lambda a, b: a + b, lista)

def multiplicacion(lista):
    return reduce(lambda a, b: a * b, lista)

def filtrar_pares(lista):
    return list(filter(lambda x: x % 2 == 0, lista))

def cuadrados(lista):
    return list(map(lambda x: x ** 2, lista))


# ---------------- PROCESAR TAREA ----------------

def procesar_tarea(tarea):
    operacion = tarea.get("operacion")
    datos = tarea.get("datos")

    if operacion == "suma":
        resultado = suma(datos)

    elif operacion == "multiplicacion":
        resultado = multiplicacion(datos)

    elif operacion == "filtrar_pares":
        resultado = filtrar_pares(datos)

    elif operacion == "cuadrados":
        resultado = cuadrados(datos)

    else:
        resultado = "ERROR: operación no válida"

    return {
        "cliente": tarea.get("cliente", "Desconocido"),
        "operacion": operacion,
        "datos_recibidos": datos,
        "resultado": resultado
    }


# ---------------- MANEJAR CLIENTE ----------------

def manejar_cliente(conn, addr):
    print(f"[NUEVO CLIENTE] {addr}")

    try:
        while True:
            data = conn.recv(4096).decode("utf-8")

            if not data:
                break

            tarea = json.loads(data)
            print(f"[TAREA RECIBIDA] {tarea}")

            respuesta = procesar_tarea(tarea)

            conn.send(json.dumps(respuesta).encode("utf-8"))

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")

    finally:
        conn.close()
        print(f"[DESCONECTADO] {addr}")


# ---------------- SERVIDOR PRINCIPAL ----------------

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