import socket
import threading
import time
from tqdm import tqdm
import os
import pickle  # Para guardar y cargar el estado

# Configuración del nodo y del Tracker
TRACKER_IP = "10.86.15.199"  # Cambiar por la IP del Tracker
TRACKER_PORT = 12345
NODO_IP = "10.86.15.250"  # Cambiar por la IP de este nodo (Nodo B)
NODO_PORT = 5001
ARCHIVOS = []  # Nodo B no comparte archivos inicialmente

# Archivo para guardar el estado
ESTADO_DESCARGA = "estado_descarga.pkl"

# Progreso de descargas (archivo -> porcentaje)
descargas = {}

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
        print(f"[Nodo B] Respuesta del Tracker: {respuesta}")


def solicitar_peers(archivo):
    """
    Solicita la lista de peers que tienen un archivo específico.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TRACKER_IP, TRACKER_PORT))
        mensaje = f"SOLICITAR:{archivo}"
        s.send(mensaje.encode())
        respuesta = s.recv(1024).decode()
        print(f"[Nodo B] Peers para {archivo}: {respuesta}")
        return respuesta.replace("PEERS:", "").split(";")  # Lista de peers


def solicitar_estado_red():
    """
    Solicita el estado de la red al Tracker.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TRACKER_IP, TRACKER_PORT))
        mensaje = "ESTADO:"
        s.send(mensaje.encode())
        estado = s.recv(4096).decode()
        print("[Nodo B] Estado de la red:")
        print(estado)


def guardar_estado():
    """
    Guarda el estado actual de las descargas en un archivo.
    """
    with open(ESTADO_DESCARGA, "wb") as f:
        pickle.dump(descargas, f)
    print("[Nodo B] Estado guardado.")


def cargar_estado():
    """
    Carga el estado previo de las descargas, si existe.
    """
    global descargas
    if os.path.exists(ESTADO_DESCARGA):
        with open(ESTADO_DESCARGA, "rb") as f:
            descargas = pickle.load(f)
        print("[Nodo B] Estado cargado.")
    else:
        print("[Nodo B] No se encontró un estado previo.")


def descargar_archivo(archivo, peers):
    """
    Descarga un archivo desde los peers.
    """
    global descargas
    if not peers or peers == ['']:
        print(f"[Nodo B] No hay peers disponibles para {archivo}.")
        return

    fragmento_tamano = 10  # Tamaño del fragmento (en %)
    progreso = descargas.get(archivo, 0)
    barra = tqdm(total=100, initial=progreso, desc=f"Descargando {archivo}")

    # Abre el archivo en modo escritura binaria
    with open(archivo, "ab") as f:  # "ab" para escribir desde el último fragmento
        while progreso < 100:
            for peer in peers:
                if progreso >= 100:
                    print(f"[Nodo B] Archivo {archivo} descargado completamente.")
                    break

                try:
                    print(f"[Nodo B] Intentando conectar con el peer: {peer}")
                    ip, port = peer.split(":")
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((ip, int(port)))
                        print(f"[Nodo B] Conectado con el peer: {peer}")
                        mensaje = f"DESCARGAR:{archivo},{progreso}"
                        s.send(mensaje.encode())
                        fragmento = s.recv(1024)
                        f.write(fragmento)  # Escribe el fragmento en el archivo
                        progreso += fragmento_tamano
                        descargas[archivo] = progreso
                        barra.update(fragmento_tamano)

                        # Guardar el progreso después de cada fragmento
                        guardar_estado()

                        # Notificar progreso al Tracker
                        notificar_progreso(archivo, progreso)
                except Exception as e:
                    print(f"[Nodo B] Error al conectar con {peer}: {e}")
    barra.close()


def notificar_progreso(archivo, progreso):
    """
    Notifica al Tracker el progreso de descarga.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TRACKER_IP, TRACKER_PORT))
        mensaje = f"ACTUALIZAR:{NODO_IP}:{NODO_PORT},{archivo},{progreso}"
        s.send(mensaje.encode())
        respuesta = s.recv(1024).decode()
        print(f"[Nodo B] Progreso notificado al Tracker: {respuesta}")


def iniciar_servidor():
    """
    Inicia el servidor del nodo para responder a descargas.
    """
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((NODO_IP, NODO_PORT))
    servidor.listen(5)
    print(f"[Nodo B] Servidor iniciado en {NODO_IP}:{NODO_PORT}")

    while True:
        conexion, direccion = servidor.accept()
        conexion.close()


def descargar_todos_los_archivos(archivos):
    """
    Descarga múltiples archivos de forma paralela.
    """
    threads = []
    for archivo in archivos:
        peers = solicitar_peers(archivo)
        hilo = threading.Thread(target=descargar_archivo, args=(archivo, peers))
        threads.append(hilo)
        hilo.start()

    for hilo in threads:
        hilo.join()


if __name__ == "__main__":
    # Cargar el estado previo
    cargar_estado()

    # Registrar nodo en el Tracker
    registrar_nodo()

    # Iniciar servidor en un hilo
    servidor_hilo = threading.Thread(target=iniciar_servidor, daemon=True)
    servidor_hilo.start()

    # Mostrar el estado de la red
    solicitar_estado_red()

    # Lista de archivos a descargar
    archivos_solicitados = ["file1.txt", "file2.mp4", "file3.png", "file4.png", "file5.txt", "file6.mp4"]

    # Descargar todos los archivos simultáneamente
    descargar_todos_los_archivos(archivos_solicitados)


