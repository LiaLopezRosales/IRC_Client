# client_network.py

import socket
import ssl
import time
from Common.irc_protocol import build_message, parse_message
from Common.custom_errors import IRCConnectionError

class ClientConnection:
    """
    Clase para manejar la conexión del cliente al servidor IRC.
    """
    def __init__(self, host, port):
        """
        Inicializa el cliente con los detalles del servidor.
        
        Args:
            host (str): Dirección del servidor.
            port (int): Puerto del servidor.
        """
        self.host = host
        self.port = port
        self.socket = None
        self.ssl_socket = None

    def connect(self):
        """
        Establece una conexión al servidor utilizando SSL.
        """
        try:
            # Crear un socket TCP/IP
            self.socket = socket.create_connection((self.host, self.port))

            # Crear un contexto SSL
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            # Aquí se carga el certificado del servidor si es necesario (no es obligatorio para el cliente)
            context.load_verify_locations(cafile="server.crt")

            # Envolver el socket en un contexto SSL
            self.ssl_socket = context.wrap_socket(self.socket, server_hostname=self.host)

            print(f"Conexión segura establecida con {self.host}:{self.port}")
        
        except Exception as e:
            raise IRCConnectionError(f"Error al conectar: {e}")

    def send(self, command, params=None, trailing=None):
        """
        Envía un mensaje al servidor en formato IRC.
        """
        try:
            message = build_message(command, params, trailing)
            self.ssl_socket.sendall(message.encode('utf-8') + b'\r\n')
        
        except Exception as e:
            raise IRCConnectionError(f"Error al enviar mensaje: {e}")

    def receive(self):
        """
        Recibe y parsea un mensaje del servidor.
        Responde automáticamente a PING.
        Procesa respuestas PONG cuando se envían PINGs.

        Returns:
            tuple: (prefix, command, params, trailing).
        """
        try:
            response = self.ssl_socket.recv(4096).decode('utf-8').strip()
            
            if response.startswith("PING"):
                # Extraer el servidor y responder con PONG
                server_name = response.split()[1]
                
                print(f"[CLIENTE] PING recibido desde {server_name}. Respondiendo con PONG.")
                
                self.pong(server_name)
                return f"PONG enviado a {server_name}"

            # elif response.startswith("PONG"):
            #     print(f"[CLIENTE] PONG recibido: {response}")
            
            return parse_message(response)
        
        except Exception as e:
            raise IRCConnectionError(f"Error al recibir mensaje: {e}")

    def join_channel(self, channel):
        """
        Envía un comando JOIN para unirse a un canal.
        
        Args:
            channel (str): Nombre del canal (e.g., "#general").
        """
        self.send("JOIN", [channel])

    def send_message(self, target, message):
        """
        Envía un mensaje privado a un usuario o canal.
        
        Args:
            target (str): Destinatario (usuario o canal).
            message (str): Contenido del mensaje.
        """
        self.send("PRIVMSG", [target], message)

    def set_user(self, username, realname):
        """
        Establece la información del usuario (RFC 2812).
        """
        self.send("USER", [username, "*", "*"], realname)

    def part_channel(self, channel):
        """
        Salir de un canal (RFC 2812).
        """
        self.send("PART", [channel])

    def quit(self, message="Saliendo del servidor"):
        """
        Desconectar del servidor con un mensaje (RFC 2812).
        """
        self.send("QUIT", trailing=message)
        self.close()

    def send_notice(self, target, message):
        """
        Enviar un mensaje de notificación sin respuesta (RFC 2812).
        """
        self.send("NOTICE", [target], message)

    def ping(self, server_name, timeout=30):
        """
        Envía un PING al servidor y espera una respuesta PONG.
        """
        try:
            self.send("PING", [server_name])
            print(f"[CLIENTE] PING enviado a {server_name}. Esperando PONG...")
            
            # # Esperar la respuesta PONG
            # response = self.receive()
            # prefix, command, params, trailing = response if isinstance(response, tuple) else ("", "", "", "")
            
            # # Validar si es un PONG válido
            # if command == "PONG" and server_name in params:
            #     print(f"[CLIENTE] PONG recibido correctamente desde {server_name}")
            # else:
            #     print(f"[CLIENTE] PONG no recibido o inválido: {response}")

            # Esperar hasta recibir el PONG
            start_time = time.time()  # Marca el tiempo de inicio
            
            while True:
                data = self.ssl_socket.recv(4096).decode('utf-8').strip()
                if data.startswith("PONG"):
                    print(f"[CLIENTE] PONG recibido: {data}")
                    break
                
                # Comprobar si ha pasado el tiempo máximo de espera
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    print(f"[ERROR] Timeout: No se recibió PONG en {timeout} segundos.")
                    break
                
                time.sleep(3)  # Espera de 1 segundo entre intentos

        except Exception as e:
            print(f"[ERROR] Error al enviar/recibir PING-PONG: {e}")

    def pong(self, server_name):
        """
        Envía un PONG al servidor en respuesta a un PING.
        """
        self.send("PONG", [server_name])
        print(f"[CLIENTE] PONG enviado al servidor: {server_name}")

    def close(self):
        """
        Cierra la conexión al servidor.
        """
        try:
            if self.ssl_socket:
                # Realizar un cierre TLS limpio
                self.ssl_socket.shutdown(socket.SHUT_RDWR)
                self.ssl_socket.close()
                
            print("Conexión cerrada.")
        
        except Exception as e:
            print(f"Error al cerrar la conexión: {e}")




