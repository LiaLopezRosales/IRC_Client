import socket
import ssl

# Conectar al servidor IRC con SSL
def connect_to_server():
    # Crear un socket TCP/IP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Crear un contexto SSL
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    
    # Envolver el socket en un contexto SSL
    ssl_socket = context.wrap_socket(client_socket, server_hostname="localhost")

    try:
        # Conectar al servidor en localhost en el puerto 6667
        ssl_socket.connect(("127.0.0.1", 6667))
        print("Conexión establecida de forma segura con el servidor.")
        
        # Recibir datos del servidor (mensaje de bienvenida)
        server_message = ssl_socket.recv(1024)
        print(f"Servidor: {server_message.decode()}")

        # Enviar un mensaje al servidor
        ssl_socket.send(b"Hola, servidor IRC seguro!")

        # Recibir respuesta del servidor
        server_response = ssl_socket.recv(1024)
        print(f"Servidor: {server_response.decode()}")
    
    except Exception as e:
        print(f"Error durante la conexión o la comunicación: {e}")
    
    finally:
        ssl_socket.close()

if __name__ == "__main__":
    connect_to_server()
