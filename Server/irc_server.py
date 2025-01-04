import socket
import ssl
from threading import Thread

class IRCServer:
    """
    Servidor IRC simulado basado en el RFC 2812 para probar cliente.
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}  # Almacena clientes como {nickname: socket}
        self.channels = {}  # {channel_name: {"users": [nicknames], "operators": [nicknames]}}

#/connect -ssl 127.0.0.1 6667

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
                    self.clients[nickname] = {
                        "socket": ssl_socket,
                        "modes": []  # Inicializar la lista de modos del usuario
                    }
                    ssl_socket.sendall(f":mock.server 001 {nickname} :Bienvenido al servidor\r\n".encode('utf-8'))
                    print(f"[SERVER] Cliente registrado con NICK: {nickname}")

                elif data.startswith("USER"):
                    ssl_socket.sendall(f":mock.server 002 {nickname} :Usuario registrado correctamente\r\n".encode('utf-8'))

                elif data.startswith("JOIN"):
                # Unirse a un canal
                    channel = data.split()[1]
                    if channel not in self.channels:
                    # Crear canal con el primer usuario como operador
                        self.channels[channel] = {"users": [nickname], "operators": [nickname]}
                        print(f"[SERVER] Canal {channel} creado por {nickname}")
                    else:
                    # Agregar usuario al canal
                        if nickname not in self.channels[channel]["users"]:
                            self.channels[channel]["users"].append(nickname)
                            ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :Bienvenido al canal {channel}\r\n".encode('utf-8'))
                            print(f"[SERVER] {nickname} se unió al canal {channel}")
                    
                    # Notificar a otros usuarios en el canal
                    for user in self.channels[channel]["users"]:
                        if user != nickname:
                            self.clients[user]["socket"].sendall(f":{nickname} JOIN {channel}\r\n".encode('utf-8'))
                    
                
                elif data.startswith("MODE"):
                    parts = data.split()
                    if len(parts) < 3:
                        ssl_socket.sendall(f":mock.server 461 {nickname} MODE :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target, mode = parts[1], parts[2]

                    # Modo aplicado a un usuario
                    if target in self.clients:
                        if mode == "+i":
                        # Establecer el modo invisible en el usuario
                            if "+i" not in self.clients[target]["modes"]:
                                self.clients[target]["modes"].append("+i")
                                ssl_socket.sendall(f":mock.server 221 {target} :Modo +i activado\r\n".encode('utf-8'))
                            else:
                                ssl_socket.sendall(f":mock.server 443 {target} :El modo ya está activado\r\n".encode('utf-8'))

                    # Modo aplicado a un canal
                    elif target in self.channels:
                        if len(parts) < 4:
                            ssl_socket.sendall(f":mock.server 461 {nickname} MODE :Faltan parámetros\r\n".encode('utf-8'))
                            continue

                        # Procesar modos de canal (ejemplo: +o)
                        channel, target_user = target, parts[3]
                        if mode == "+o":
                            if nickname in self.channels[channel]["operators"]:
                                if target_user not in self.channels[channel]["operators"]:
                                    self.channels[channel]["operators"].append(target_user)
                                    ssl_socket.sendall(f":mock.server 324 {channel} {target_user} :Ahora es operador\r\n".encode('utf-8'))
                                else:
                                    ssl_socket.sendall(f":mock.server 443 {channel} {target_user} :Ya es operador\r\n".encode('utf-8'))
                            else:
                                ssl_socket.sendall(f":mock.server 482 {channel} :No tienes permisos para cambiar modos\r\n".encode('utf-8'))

                    else:
                        ssl_socket.sendall(f":mock.server 401 {nickname} {target} :El objetivo no existe\r\n".encode('utf-8'))


                elif data.startswith("PART"):
                    channel = data.split()[1]
                    if channel in self.channels and nickname in self.channels[channel]["users"]:
                        self.channels[channel]["users"].remove(nickname)
                        ssl_socket.sendall(f":mock.server 333 {nickname} {channel} :{nickname} ha salido del canal\r\n".encode('utf-8'))
                        print(f"[SERVER] {nickname} ha salido del canal {channel}")

                        # Notificar a otros usuarios en el canal
                        for user in self.channels[channel]["users"]:
                            self.clients[user]["socket"].sendall(f":{nickname} PART {channel}\r\n".encode('utf-8'))

                        # Eliminar el canal si no quedan usuarios
                        if not self.channels[channel]["users"]:
                            print(f"[SERVER] Canal {channel} eliminado porque está vacío.")
                            del self.channels[channel]

                    else:
                    # Responder con un error si el usuario no está en el canal
                        ssl_socket.sendall(f":mock.server 442 {nickname} {channel} :No estás en el canal\r\n".encode('utf-8'))
                    
                
                elif data.startswith("LIST"):
                    # Listar canales
                    if self.channels:
                        for channel, details in self.channels.items():
                            ssl_socket.sendall(f":mock.server 322 {nickname} {channel} {len(details['users'])} :Usuarios en el canal\r\n".encode('utf-8'))
                        ssl_socket.sendall(b":mock.server 323 :Fin de la lista de canales\r\n")
                    else:
                        ssl_socket.sendall(b":mock.server 323 :No hay canales disponibles\r\n")

                elif data.startswith("PRIVMSG"):
                    parts = data.split(' ', 2)
                    target = parts[1]
                    message = parts[2][1:] if len(parts) > 2 else "(sin mensaje)"
                    if target.startswith("#"):  # Mensaje a un canal
                        if target in self.channels:
                            for user in self.channels[target]["users"]:
                                if user != nickname:
                                    self.clients[user]["socket"].sendall(f":{nickname} PRIVMSG {target} :{message}\r\n".encode('utf-8'))
                            print(f"[SERVER] Mensaje enviado a canal {target}: {message}")
                        else:
                            ssl_socket.sendall(f":mock.server 403 {target} :No existe el canal\r\n".encode('utf-8'))
                    else:  # Mensaje privado a un usuario
                        if target in self.clients:
                            self.clients[target].sendall(f":{nickname} PRIVMSG {target} :{message}\r\n".encode('utf-8'))
                            print(f"[SERVER] Mensaje enviado a usuario {target}: {message}")
                        else:
                            ssl_socket.sendall(f":mock.server 401 {target} :El usuario no está conectado\r\n".encode('utf-8'))
                    

                elif data.startswith("NOTICE"):
                    parts = data.split(' ', 2)
                    target = parts[1]
                    message = parts[2][1:] if len(parts) > 2 else "(sin mensaje)"
                    if target in self.clients:
                        self.clients[target].sendall(f":{nickname} NOTICE {target} :{message}\r\n".encode('utf-8'))
                    print(f"[SERVER] Notificación enviada a {target}: {message}")

                elif data.startswith("PING"):
                    server_name = data.split()[1]
                    ssl_socket.sendall(f"PONG {server_name}\r\n".encode('utf-8'))
                    print(f"[SERVER] PING recibido, PONG enviado a {nickname}")

                elif data.startswith("PONG"):
                    print(f"[SERVER] PONG recibido de {nickname}")

                elif data.startswith("QUIT"):
                    reason = data.split(":", 1)[1] if ":" in data else "Desconexión voluntaria"
                    print(f"[SERVER] {nickname} se ha desconectado: {reason}")
                    ssl_socket.sendall(f":mock.server 221 {nickname} QUIT :{reason}\r\n".encode('utf-8'))

                    # Notificar a otros usuarios en los canales
                    for channel, details in self.channels.items():
                        if nickname in details["users"]:
                            details["users"].remove(nickname)
                            if not details["users"]:
                                del self.channels[channel]
                            else:
                                for user in details["users"]:
                                    self.clients[user].sendall(f":{nickname} QUIT :{reason}\r\n".encode('utf-8'))
                    
                    break

                else:
                    ssl_socket.sendall(b":mock.server 421 Unknown command\r\n")
                    print(f"[SERVER] Comando desconocido recibido: {data}")

        except Exception as e:
            print(f"[ERROR] Error con cliente {addr}: {e}")

        finally:
            if nickname and nickname in self.clients:
                del self.clients[nickname]
            try:
                ssl_socket.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                print(f"[!] Error al cerrar la conexión SSL: {e}")
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
