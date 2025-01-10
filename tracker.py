import socket
import threading

# Configuración del Tracker
TRACKER_IP = "0.0.0.0"  # Escuchar en todas las interfaces
TRACKER_PORT = 12345
nodos = {}  # Diccionario para almacenar nodos y sus datos: {IP: {puerto, archivos, estado}}

def manejar_conexion(cliente):
    """
    Maneja las solicitudes de los nodos.
    """
    try:
        mensaje = cliente.recv(1024).decode()
        print(f"[Tracker] Mensaje recibido: {mensaje}")
        comando, datos = mensaje.split(":", 1)

        if comando == "REGISTRAR":
            registrar_nodo(datos)
            cliente.send("Registro exitoso.".encode())
        elif comando == "SOLICITAR":
            archivo = datos
            peers = solicitar_peers(archivo)
            cliente.send(f"PEERS:{';'.join(peers)}".encode())
        elif comando == "ACTUALIZAR":
            actualizar_estado(datos)
            cliente.send("Progreso actualizado.".encode())
        elif comando == "ESTADO":
            estado_red = mostrar_estado_red()
            cliente.send(estado_red.encode())
    except Exception as e:
        print(f"[Tracker] Error al manejar conexión: {e}")
    finally:
        cliente.close()


def registrar_nodo(datos):
    """
    Registra un nodo en el Tracker.
    """
    ip, puerto, archivos = datos.split(",")
    archivos = archivos.split(";") if archivos else []
    nodos[ip] = {"puerto": puerto, "archivos": archivos, "estado": "Activo"}
    print(f"[Tracker] Nodo registrado: {ip}:{puerto} - Archivos: {archivos}")


def solicitar_peers(archivo):
    """
    Devuelve la lista de nodos que tienen un archivo.
    """
    peers = []
    for ip, info in nodos.items():
        if archivo in info["archivos"]:
            peers.append(f"{ip}:{info['puerto']}")
    return peers


def actualizar_estado(datos):
    """
    Actualiza el estado de un nodo en el Tracker.
    """
    ip, archivo, progreso = datos.split(",")
    if ip in nodos:
        nodos[ip]["estado"] = f"Descargando {archivo}: {progreso}%"
        print(f"[Tracker] Progreso actualizado: {ip} - {archivo} {progreso}%")


def mostrar_estado_red():
    """
    Devuelve el estado actual de la red.
    """
    estado = "[Tracker] Estado de la red:\n"
    for ip, info in nodos.items():
        estado += f"- Nodo: {ip}:{info['puerto']}\n"
        estado += f"  Archivos compartidos: {', '.join(info['archivos'])}\n"
        estado += f"  Estado: {info['estado']}\n"
    print(estado)
    return estado


def iniciar_tracker():
    """
    Inicia el servidor del Tracker.
    """
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((TRACKER_IP, TRACKER_PORT))
    servidor.listen(5)
    print(f"[Tracker] Servidor iniciado en {TRACKER_IP}:{TRACKER_PORT}")

    while True:
        cliente, direccion = servidor.accept()
        print(f"[Tracker] Conexión establecida con {direccion}")
        hilo = threading.Thread(target=manejar_conexion, args=(cliente,))
        hilo.start()


if __name__ == "__main__":
    iniciar_tracker()
