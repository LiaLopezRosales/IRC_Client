from Server.irc_server import IRCServer
from Common.shared_constants import DEFAULT_HOST, DEFAULT_PORT

def run_server():
    try:
        server = IRCServer(DEFAULT_HOST, DEFAULT_PORT)
        print("Servidor IRC en ejecución...")
        server.start()
        server._accept_clients()
        server._handle_client()
    except KeyboardInterrupt:
        print("Servidor detenido manualmente.")
    except Exception as e:
        print(f"Error en el servidor: {e}")
        
run_server()
