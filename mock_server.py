import socket
import ssl
from threading import Thread

class MockIRCServer:
    """
    Servidor IRC simulado basado en el RFC 2812 para probar cliente.
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}  # Almacena clientes como {nickname: socket}

    def start(self):
        """
        Inicia el servidor en un hilo separado.
        """
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[SERVER] Servidor simulado escuchando en {self.host}:{self.port}")

        Thread(target=self._accept_clients, daemon=True).start()

    def _accept_clients(self):
        """
        Acepta y gestiona conexiones de clientes.
        """
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"[SERVER] Cliente conectado desde {addr}")

                # Configurar SSL
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(certfile="server.crt", keyfile="server.key")

                ssl_socket = context.wrap_socket(client_socket, server_side=True)
                Thread(target=self._handle_client, args=(ssl_socket, addr), daemon=True).start()
            except Exception as e:
                print(f"[ERROR] Error al aceptar cliente: {e}")

    def _handle_client(self, ssl_socket, addr):
        """
        Maneja comandos del cliente basado en RFC 2812.
        """
        try:
            nickname = None
            while self.running:
                data = ssl_socket.recv(4096).decode('utf-8').strip()
                if not data:
                    break

                print(f"[SERVER] Mensaje recibido: {data}")

                # Procesar comandos
                if data.startswith("NICK"):
                    nickname = data.split()[1]
                    self.clients[nickname] = ssl_socket
                    ssl_socket.sendall(f":mock.server 001 {nickname} :Bienvenido al servidor\r\n".encode('utf-8'))
                    print(f"[SERVER] Cliente registrado con NICK: {nickname}")

                elif data.startswith("USER"):
                    ssl_socket.sendall(f":mock.server 002 {nickname} :Usuario registrado correctamente\r\n".encode('utf-8'))

                elif data.startswith("JOIN"):
                    channel = data.split()[1]
                    ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :Bienvenido al canal {channel}\r\n".encode('utf-8'))
                    print(f"[SERVER] {nickname} se unió al canal {channel}")

                elif data.startswith("PART"):
                    channel = data.split()[1]
                    ssl_socket.sendall(f":mock.server 333 {nickname} {channel} :{nickname} ha salido del canal\r\n".encode('utf-8'))
                    print(f"[SERVER] {nickname} ha salido del canal {channel}")

                elif data.startswith("PRIVMSG"):
                    parts = data.split(' ', 2)
                    target = parts[1]
                    message = parts[2][1:] if len(parts) > 2 else "(sin mensaje)"
                    print(f"[SERVER] PRIVMSG de {nickname} a {target}: {message}")
                    ssl_socket.sendall(f":mock.server 200 {nickname} PRIVMSG {target} :{message}\r\n".encode('utf-8'))

                elif data.startswith("NOTICE"):
                    parts = data.split(' ', 2)
                    target = parts[1]
                    message = parts[2][1:] if len(parts) > 2 else "(sin mensaje)"
                    print(f"[SERVER] NOTICE de {nickname} a {target}: {message}")

                elif data.startswith("PING"):
                    server_name = data.split()[1]
                    ssl_socket.sendall(f"PONG {server_name}\r\n".encode('utf-8'))
                    print(f"[SERVER] PING recibido, PONG enviado a {nickname}")

                elif data.startswith("PONG"):
                    print(f"[SERVER] PONG recibido de {nickname}")

                elif data.startswith("QUIT"):
                    ssl_socket.sendall(f":mock.server 221 {nickname} QUIT :Desconexión voluntaria\r\n".encode('utf-8'))
                    print(f"[SERVER] {nickname} se ha desconectado.")
                    break

                else:
                    ssl_socket.sendall(b":mock.server 421 Unknown command\r\n")
                    print(f"[SERVER] Comando desconocido recibido: {data}")

        except Exception as e:
            print(f"[ERROR] Error con cliente {addr}: {e}")

        finally:
            ssl_socket.shutdown(socket.SHUT_RDWR)
            ssl_socket.close()
            print(f"[SERVER] Conexión cerrada con {addr}")

    def stop(self):
        """
        Detiene el servidor.
        """
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("[SERVER] Servidor detenido correctamente.")
