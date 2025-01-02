import socket
import ssl
from custom_errors import IRCConnectionError

class ClientConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        try:
            raw_socket = socket.create_connection((self.host, self.port))
            self.socket = ssl.wrap_socket(raw_socket)
        except Exception as e:
            raise IRCConnectionError(f"Error al conectar: {e}")

    def send(self, message):
        try:
            self.socket.sendall(message.encode('utf-8'))
        except Exception as e:
            raise IRCConnectionError(f"Error al enviar mensaje: {e}")

    def receive(self):
        try:
            return self.socket.recv(4096).decode('utf-8')
        except Exception as e:
            raise IRCConnectionError(f"Error al recibir mensaje: {e}")
