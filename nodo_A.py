import socket
import threading
import time

# Configuración del nodo y del Tracker
TRACKER_IP = "10.86.15.199"  # Cambiar por la IP del Tracker
TRACKER_PORT = 12345
NODO_IP = "10.86.15.249"  # Cambiar por la IP de este nodo (Nodo A)
NODO_PORT = 5000
ARCHIVOS = ["file1.txt", "file2.mp4", "file3.png", "file4.png", "file5.txt", "file6.mp4"]  # Archivos compartidos por este nodo

def registrar_nodo():
    """
    Se registra este nodo en el Tracker.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TRACKER_IP, TRACKER_PORT))
        archivos_str = ";".join(ARCHIVOS)
        mensaje = f"REGISTRAR:{NODO_IP},{NODO_PORT},{archivos_str}"
        s.send(mensaje.encode())
        respuesta = s.recv(1024).decode()
        print(f"[Nodo A] Respuesta del Tracker: {respuesta}")


def manejar_peticion(conexion):
    """
    Maneja una petición de descarga desde otro nodo.
    """
    try:
        mensaje = conexion.recv(1024).decode()
        print(f"[Nodo A] Solicitud recibida: {mensaje}")
        comando, datos = mensaje.split(":", 1)

        if comando == "DESCARGAR":
            archivo, progreso = datos.split(",")
            if archivo in ARCHIVOS:
                fragmento = f"Fragmento desde {progreso}%"
                conexion.send(fragmento.encode())
                print(f"[Nodo A] Fragmento de {archivo} enviado.")
            else:
                conexion.send("Archivo no disponible.".encode())
                print(f"[Nodo A] Archivo solicitado no disponible: {archivo}")
    except Exception as e:
        print(f"[Nodo A] Error al manejar petición: {e}")
    finally:
        conexion.close()


def iniciar_servidor():
    """
    Inicia el servidor del nodo para responder a descargas.
    """
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((NODO_IP, NODO_PORT))
    servidor.listen(5)
    print(f"[Nodo A] Servidor iniciado en {NODO_IP}:{NODO_PORT}")

    while True:
        conexion, direccion = servidor.accept()
        print(f"[Nodo A] Conexión establecida con {direccion}")
        hilo = threading.Thread(target=manejar_peticion, args=(conexion,))
        hilo.start()


if __name__ == "__main__":
    # Registrar nodo en el Tracker
    registrar_nodo()

    # Iniciar servidor en un hilo para que corra indefinidamente
    iniciar_servidor()


