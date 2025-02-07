from Server.irc_server import IRCServer
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4094

def run_server():
    try:
        # Crear una instancia del servidor IRC
        server = IRCServer(DEFAULT_HOST, DEFAULT_PORT)
        print("Servidor IRC en ejecución...")
        
        # Iniciar el servidor (esto ejecuta _accept_clients en un hilo separado)
        server.start()
        
        # Mantener el programa en ejecución
        while True:
            time.sleep(1)  # Evitar que el programa termine
    except KeyboardInterrupt:
        print("Servidor detenido manualmente.")
    except Exception as e:
        print(f"Error en el servidor: {e}")
    finally:
        # Detener el servidor de manera segura
        server.stop()

if __name__ == "__main__":
    run_server()
