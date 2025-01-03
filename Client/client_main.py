from client_network import ClientConnection
from client_gui import start_gui
from Common.shared_constants import DEFAULT_HOST, DEFAULT_PORT

def run_client():
    try:
        connection = ClientConnection(DEFAULT_HOST, DEFAULT_PORT)
        connection.connect()  # Inicia la conexión
        start_gui(connection)  # Lanza la interfaz gráfica
    except Exception as e:
        print(f"Error al iniciar el cliente: {e}")
