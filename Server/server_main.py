from server_handler import IRCServer
from shared_constants import DEFAULT_HOST, DEFAULT_PORT

def run_server():
    try:
        server = IRCServer((DEFAULT_HOST, DEFAULT_PORT))
        print("Servidor IRC en ejecución...")
        server.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido manualmente.")
    except Exception as e:
        print(f"Error en el servidor: {e}")
