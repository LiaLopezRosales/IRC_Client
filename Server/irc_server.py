import socket
import ssl
from threading import Thread
import time
import uuid


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
        self.whowas = {}    # {nickname: {...}} para almacenar usuarios desconectados
        self.ping_interval = 30  # Segundos entre PINGs
        self.ping_timeout = 280  # Tiempo máximo sin PONG antes de desconectar
        self.pending_users = {}

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
        Thread(target=self._send_pings, daemon=True).start()
        Thread(target=self._check_inactive_clients, daemon=True).start()
        
    def _send_pings(self):
        """Envía PINGs periódicos a los clientes."""
        while self.running:
            time.sleep(self.ping_interval)
            current_time = time.time()
            for nick, data in list(self.clients.items()):
                try:
                    # Usar el nombre del servidor como token
                    token = str(uuid.uuid4())  # Genera un UUID único para cada PING
                    data["socket"].sendall(f"PING :{token}\r\n".encode("utf-8"))
                    data["ping_token"] = token  # Almacenar el nombre del servidor
                    data["last_ping_sent"] = current_time
                except Exception as e:
                    print(f"[ERROR] Error enviando PING a {nick}: {e}")
                        
    def _check_inactive_clients(self):
        """Desconecta clientes inactivos."""
        while self.running:
            time.sleep(100)
            current_time = time.time()
            to_remove = []
            for nick, data in list(self.clients.items()):
                last_pong = data.get("last_pong", 0)
                last_ping = data.get("last_ping_sent", 0)
                # Verificar si no ha respondido al PING o no se ha enviado PING
                if (current_time - last_pong > self.ping_timeout) or (
                    current_time - last_ping > self.ping_timeout
                ):
                    print(f"[SERVER] Desconectando a {nick} por inactividad")
                    to_remove.append(nick)
            for nick in to_remove:
                self._disconnect_client(nick, "Ping timeout")
                
    def _disconnect_client(self, nick, reason):
        """Limpia los datos del cliente desconectado."""
        if nick in self.clients:
            try:
                self.clients[nick]["socket"].close()
            except:
                pass
            del self.clients[nick]
            # Limpiar canales y WHOWAS
            for channel in list(self.channels.keys()):
                if nick in self.channels[channel]["users"]:
                    self.channels[channel]["users"].remove(nick)
                    if nick in self.channels[channel]["operators"]:
                        self.channels[channel]["operators"].remove(nick)
                    if not self.channels[channel]["users"]:
                        del self.channels[channel]
            print(f"[SERVER] {nick} desconectado: {reason}")

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
                
    def _complete_registration(self, nick, ssl_socket):
        """Envía mensajes de bienvenida tras NICK + USER exitosos."""
        user_info = self.pending_users.get(ssl_socket)
        if user_info:
            self.clients[nick]["username"] = user_info["username"]
            self.clients[nick]["realname"] = user_info["realname"]
            # Limpiar datos temporales
            del self.pending_users[ssl_socket]
        
        # Mensajes de registro
        welcome_msgs = [
            f":mock.server 001 {nick} :Bienvenido al servidor",
            f":mock.server 002 {nick} :Tu host es mock.server",
            f":mock.server 003 {nick} :Este servidor fue creado hoy",
            f":mock.server 004 {nick} mock.server 1.0 o o"
        ]
        for msg in welcome_msgs:
            ssl_socket.sendall(f"{msg}\r\n".encode('utf-8'))
        print(f"[SERVER] Cliente {nick} registrado completamente")

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
                    parts = data.split()
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 431 :No se proporcionó un nickname\r\n".encode('utf-8'))
                        continue

                    new_nick = parts[1]

                    # Verificar si el NICK ya está en uso
                    if new_nick in self.clients:
                        ssl_socket.sendall(f":mock.server 433 * {new_nick} :El apodo ya está en uso\r\n".encode('utf-8'))
                        print(f"[SERVER] NICK rechazado: {new_nick} ya está en uso")
                        continue

                    # Si el usuario ya tiene un nick registrado (cambio de nick)
                    if nickname and nickname in self.clients:
                        old_nick = nickname

                        # Guardar el nick antiguo en WHOWAS
                        user_data = {
                            "nickname": old_nick,
                            "username": self.clients[old_nick].get("username", "~user"),
                            "hostname": self.clients[old_nick].get("hostname", addr[0]),  # Usar hostname almacenado
                            "realname": self.clients[old_nick].get("realname", "Desconocido"),
                            "disconnected_time": time.time()
                        }

                        if old_nick not in self.whowas:
                            self.whowas[old_nick] = []
                        self.whowas[old_nick].insert(0, user_data)
                        if len(self.whowas[old_nick]) > 10:
                            self.whowas[old_nick].pop()

                        # Actualizar el nick en el diccionario
                        self.clients[new_nick] = self.clients.pop(old_nick)
                        nickname = new_nick
                        ssl_socket.sendall(f":{old_nick} NICK {new_nick}\r\n".encode('utf-8'))
                        print(f"[SERVER] {old_nick} cambió su nick a {new_nick}")

                    else:
                        self.clients[new_nick] = {
                            "socket": ssl_socket,
                            "modes": [],
                            "username": None,
                            "realname": None,
                            "hostname": addr[0]
                        }
                        nickname = new_nick
                        print(f"[SERVER] Cliente registrado con NICK: {new_nick}")
                        
                        if ssl_socket in self.pending_users:
                            self._complete_registration(new_nick, ssl_socket)
    
                elif data.startswith("USER"):
                    parts = data.split()
                    if len(parts) < 5:
                        ssl_socket.sendall(f":mock.server 461 {nickname} USER :Faltan parámetros\r\n".encode('utf-8'))
                        print("[SERVER] Comando USER rechazado: Faltan parámetros")
                        continue

                    username = parts[1]
                    realname = " ".join(parts[4:])[1:]  # Nombre real sin el ":"
                    self.pending_users[ssl_socket] = {
                        "username": username,
                        "realname": realname
                    }

                    if nickname and nickname in self.clients:
                        self._complete_registration(nickname, ssl_socket)
                    else:
                        ssl_socket.sendall(f":mock.server 451 * :Debes registrar un NICK primero\r\n".encode('utf-8'))
                        print("[SERVER] USER recibido, esperando NICK válido")

                #No implementada autentificación ya que el servidor no tiene conexión restringida, posible extensión luego    
                elif data.startswith("PASS"):
                    parts = data.split()
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 461 {nickname} PASS :Faltan parámetros\r\n".encode('utf-8'))
                        print("[SERVER] Comando PASS rechazado: Faltan parámetros")
                        continue

                    password = parts[1]
                    # Aquí puedes agregar lógica para validar la contraseña
                    print(f"[SERVER] Cliente {nickname} envió la contraseña: {password}")
                    
                elif data.startswith("JOIN"):
                    parts = data.split()
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 461 {nickname} JOIN :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    channel = parts[1]

                    # Verificar si el canal existe
                    if channel not in self.channels:
                        # Crear canal y asignar modos por defecto (+nt)
                        self.channels[channel] = {
                            "users": [nickname],
                            "operators": [nickname],
                            "topic": None,
                            "modes": "+nt"  # +n: No mensajes externos, +t: Solo ops pueden cambiar el tema
                        }
                        print(f"[SERVER] Canal {channel} creado por {nickname}")
                    else:
                        if nickname not in self.channels[channel]["users"]:
                            self.channels[channel]["users"].append(nickname)

                    # Enviar respuestas obligatorias según RFC 2812
                    # 1. Enviar JOIN a todos los usuarios del canal
                    for user in self.channels[channel]["users"]:
                        self.clients[user]["socket"].sendall(f":{nickname}!{self.clients[nickname]['username']}@mock.server JOIN {channel}\r\n".encode('utf-8'))

                    # 2. Enviar lista de usuarios (353 RPL_NAMREPLY)
                    users_list = " ".join([f"@{u}" if u in self.channels[channel]["operators"] else u for u in self.channels[channel]["users"]])
                    ssl_socket.sendall(f":mock.server 353 {nickname} = {channel} :{users_list}\r\n".encode('utf-8'))
                    ssl_socket.sendall(f":mock.server 366 {nickname} {channel} :Fin de la lista NAMES\r\n".encode('utf-8'))

                    # 3. Enviar tema del canal (332 RPL_TOPIC o 331 RPL_NOTOPIC)
                    topic = self.channels[channel].get("topic")
                    if topic:
                        ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :{topic}\r\n".encode('utf-8'))
                    else:
                        ssl_socket.sendall(f":mock.server 331 {nickname} {channel} :No hay tema establecido\r\n".encode('utf-8'))
                                
                elif data.startswith("MODE"):
                    parts = data.split()
                    if len(parts) < 3:
                        ssl_socket.sendall(f":mock.server 461 {nickname} MODE :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target = parts[1]
                    mode = parts[2]

                    # Modo aplicado a un usuario
                    if target in self.clients:
                        if mode == "+i":
                            if "+i" not in self.clients[target]["modes"]:
                                self.clients[target]["modes"].append("+i")
                                ssl_socket.sendall(f":mock.server 221 {target} :Modo +i activado\r\n".encode('utf-8'))
                                print(f"[SERVER] {target} ha activado el modo +i (invisible)")
                            else:
                                ssl_socket.sendall(f":mock.server 443 {target} :El modo ya está activado\r\n".encode('utf-8'))
                        elif mode == "-i":
                            if "+i" in self.clients[target]["modes"]:
                                self.clients[target]["modes"].remove("+i")
                                ssl_socket.sendall(f":mock.server 221 {target} :Modo +i desactivado\r\n".encode('utf-8'))
                                print(f"[SERVER] {target} ha desactivado el modo +i (invisible)")
                            else:
                                ssl_socket.sendall(f":mock.server 442 {target} :El modo no estaba activado\r\n".encode('utf-8'))

                    elif target in self.channels:
                        if len(parts) < 4:
                            ssl_socket.sendall(f":mock.server 461 {nickname} MODE :Faltan parámetros\r\n".encode('utf-8'))
                            continue

                        target = parts[1]
                        mode = parts[2]
                        target_user = parts[3]  # Nombre de usuario (puede incluir "_")

                        # Modo aplicado a un canal
                        if target in self.channels:
                            channel = target

                            # Verificar si el usuario que ejecuta el comando es operador
                            if nickname not in self.channels[channel]["operators"]:
                                error_msg = f":mock.server 482 {nickname} {channel} :No tienes permisos para cambiar modos\r\n"
                                ssl_socket.sendall(error_msg.encode('utf-8'))
                                continue

                            # Manejar +o (promover a operador)
                            if mode == "+o":
                                if target_user not in self.channels[channel]["users"]:
                                    error_msg = f":mock.server 441 {target_user} {channel} :El usuario no está en el canal\r\n"
                                    ssl_socket.sendall(error_msg.encode('utf-8'))
                                elif target_user in self.channels[channel]["operators"]:
                                    error_msg = f":mock.server 443 {channel} {target_user} :Ya es operador\r\n"
                                    ssl_socket.sendall(error_msg.encode('utf-8'))
                                else:
                                    self.channels[channel]["operators"].append(target_user)
                                    # Notificar a TODOS en el canal
                                    message = f":{nickname}!{self.clients[nickname]['username']}@mock.server MODE {channel} +o {target_user}\r\n"
                                    for user in self.channels[channel]["users"]:
                                        self.clients[user]["socket"].sendall(message.encode('utf-8'))

                            # Manejar -o (quitar operador)
                            elif mode == "-o":
                                if target_user not in self.channels[channel]["operators"]:
                                    error_msg = f":mock.server 441 {channel} {target_user} :El usuario no era operador\r\n"
                                    ssl_socket.sendall(error_msg.encode('utf-8'))
                                else:
                                    self.channels[channel]["operators"].remove(target_user)
                                    # Notificar a TODOS en el canal
                                    message = f":{nickname}!{self.clients[nickname]['username']}@mock.server MODE {channel} -o {target_user}\r\n"
                                    for user in self.channels[channel]["users"]:
                                        self.clients[user]["socket"].sendall(message.encode('utf-8'))
                    
                                 
                elif data.startswith("PART"):
                    parts = data.split()
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 461 {nickname} PART :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    channel = parts[1]
                    if channel in self.channels and nickname in self.channels[channel]["users"]:
                        # Notificar a todos en el canal
                        for user in self.channels[channel]["users"]:
                            self.clients[user]["socket"].sendall(f":{nickname}!{self.clients[nickname]['username']}@mock.server PART {channel}\r\n".encode('utf-8'))

                        # Eliminar al usuario del canal
                        self.channels[channel]["users"].remove(nickname)
                        if nickname in self.channels[channel]["operators"]:
                            self.channels[channel]["operators"].remove(nickname)

                        # Eliminar el canal si está vacío
                        if not self.channels[channel]["users"]:
                            del self.channels[channel]
                            print(f"[SERVER] Canal {channel} eliminado porque está vacío.")

                    else:
                        ssl_socket.sendall(f":mock.server 442 {nickname} {channel} :No estás en el canal\r\n".encode('utf-8'))
                                
                elif data.startswith("TOPIC"):
                    parts = data.split(' ', 2)  # Dividir en máximo 3 partes
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 461 {nickname} TOPIC :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    channel = parts[1]
                    if channel not in self.channels:
                        ssl_socket.sendall(f":mock.server 403 {nickname} {channel} :No existe el canal\r\n".encode('utf-8'))
                        continue

                    # Consulta del tema actual
                    if len(parts) == 2:
                        topic = self.channels[channel].get("topic")
                        if topic:
                            ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :{topic}\r\n".encode('utf-8'))
                        else:
                            ssl_socket.sendall(f":mock.server 331 {nickname} {channel} :No hay tema establecido\r\n".encode('utf-8'))
                        continue

                    # Establecer o eliminar tema
                    new_topic = parts[2].strip()
                    if nickname not in self.channels[channel]["operators"]:
                        ssl_socket.sendall(f":mock.server 482 {channel} :No tienes permisos para cambiar el tema\r\n".encode('utf-8'))
                        continue

                    if new_topic == ":":
                        self.channels[channel]["topic"] = None
                        # Notificar a todos en el canal
                        for user in self.channels[channel]["users"]:
                            self.clients[user]["socket"].sendall(
                                f":{nickname}!{self.clients[nickname]['username']}@mock.server TOPIC {channel} :\r\n".encode('utf-8')
                            )
                        ssl_socket.sendall(f":mock.server 331 {nickname} {channel} :Tema eliminado\r\n".encode('utf-8'))
                    else:
                        self.channels[channel]["topic"] = new_topic.lstrip(':')
                        # Notificar a todos en el canal
                        for user in self.channels[channel]["users"]:
                            self.clients[user]["socket"].sendall(
                                f":{nickname}!{self.clients[nickname]['username']}@mock.server TOPIC {channel} :{new_topic.lstrip(':')}\r\n".encode('utf-8')
                            )
                        ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :{new_topic.lstrip(':')}\r\n".encode('utf-8'))
                        
                elif data.startswith("KICK"):
                    parts = data.split(' ', 3)
                    if len(parts) < 3:
                        ssl_socket.sendall(f":mock.server 461 {nickname} KICK :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    channel = parts[1]
                    target = parts[2]
                    reason = parts[3][1:] if len(parts) > 3 else "Expulsado por un operador"

                    if channel not in self.channels:
                        ssl_socket.sendall(f":mock.server 403 {nickname} {channel} :No existe el canal\r\n".encode('utf-8'))
                        continue

                    if nickname not in self.channels[channel]["operators"]:
                        ssl_socket.sendall(f":mock.server 482 {channel} :No tienes permisos para expulsar usuarios\r\n".encode('utf-8'))
                        continue

                    if target not in self.channels[channel]["users"]:
                        ssl_socket.sendall(f":mock.server 441 {nickname} {target} :El usuario no está en el canal\r\n".encode('utf-8'))
                        continue

                    # Notificar al expulsado y al canal
                    kick_message = f":{nickname}!{self.clients[nickname]['username']}@mock.server KICK {channel} {target} :{reason}\r\n"
                    for user in self.channels[channel]["users"]:
                        self.clients[user]["socket"].sendall(kick_message.encode('utf-8'))

                    # Eliminar al usuario del canal
                    self.channels[channel]["users"].remove(target)
                    if target in self.channels[channel]["operators"]:
                        self.channels[channel]["operators"].remove(target)
                        
                elif data.startswith("INVITE"):
                    parts = data.split()
                    if len(parts) < 3:
                        ssl_socket.sendall(f":mock.server 461 {nickname} INVITE :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target = parts[1]
                    channel = parts[2]

                    if channel not in self.channels:
                        ssl_socket.sendall(f":mock.server 403 {nickname} {channel} :No existe el canal\r\n".encode('utf-8'))
                        continue

                    if target not in self.clients:
                        ssl_socket.sendall(f":mock.server 401 {nickname} {target} :El usuario no está conectado\r\n".encode('utf-8'))
                        continue

                    # Enviar invitación al usuario
                    self.clients[target]["socket"].sendall(
                        f":{nickname}!{self.clients[nickname]['username']}@mock.server INVITE {target} :{channel}\r\n".encode('utf-8')
                    )
                    ssl_socket.sendall(f":mock.server 341 {nickname} {target} {channel} :Invitación enviada\r\n".encode('utf-8'))
                    
                elif data.startswith("WHOIS"):
                    parts = data.split()
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 461 {nickname} WHOIS :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target = parts[1]
                    if target not in self.clients:
                        ssl_socket.sendall(f":mock.server 401 {nickname} {target} :El usuario no está conectado\r\n".encode('utf-8'))
                        continue

                    # Obtener información del usuario
                    user_info = self.clients[target]
                    username = user_info.get("username", "*")
                    hostname = "127.0.0.1"  # Puedes cambiar esto por el host real del usuario
                    realname = user_info.get("realname", "Desconocido")
                    server_name = "mock.server"
                    idle_time = "0"  # Tiempo de inactividad (puedes implementar esto si es necesario)

                    # Enviar respuesta WHOISUSER (311)
                    ssl_socket.sendall(
                        f":mock.server 311 {nickname} {target} {username} {hostname} * :{realname}\r\n".encode('utf-8')
                    )

                    # Enviar respuesta WHOISSERVER (312)
                    ssl_socket.sendall(
                        f":mock.server 312 {nickname} {target} {server_name} :Información del servidor\r\n".encode('utf-8')
                    )

                    # Enviar respuesta WHOISIDLE (317)
                    ssl_socket.sendall(
                        f":mock.server 317 {nickname} {target} {idle_time} :Segundos inactivo\r\n".encode('utf-8')
                    )

                    # Enviar respuesta ENDOFWHOIS (318)
                    ssl_socket.sendall(
                        f":mock.server 318 {nickname} {target} :Fin de la lista WHOIS\r\n".encode('utf-8')
                    )
                    
                elif data.startswith("WHOWAS"):
                    parts = data.split()
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 406 {nickname} :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target = parts[1]
                    if target not in self.whowas or not self.whowas[target]:
                        ssl_socket.sendall(f":mock.server 406 {nickname} {target} :No hay información histórica\r\n".encode('utf-8'))
                        continue

                    # Enviar todas las entradas históricas del usuario
                    for entry in self.whowas[target]:
                        ssl_socket.sendall(
                            f":mock.server 314 {nickname} {entry['nickname']} {entry['username']} {entry['hostname']} * :{entry['realname']}\r\n".encode('utf-8')
                        )
                    ssl_socket.sendall(f":mock.server 369 {nickname} {target} :Fin de la lista WHOWAS\r\n".encode('utf-8'))
                    
                elif data.startswith("WHO"):
                    parts = data.split()
                    channel = parts[1] if len(parts) > 1 else None

                    # WHO sin parámetros: listar usuarios no invisibles en todo el servidor
                    if not channel:
                        for user, details in self.clients.items():
                            if "+i" not in details["modes"]:
                                username = details.get("username", "~user")
                                flags = "H"  # H = Usuario disponible (no away)
                                ssl_socket.sendall(
                                    f":mock.server 352 {nickname} * {username} {self.host} mock.server {user} {flags} :0 {details['realname']}\r\n".encode('utf-8')
                                )
                        ssl_socket.sendall(f":mock.server 315 {nickname} * :Fin de la lista WHO\r\n".encode('utf-8'))
                        continue

                    # WHO para un canal específico
                    if channel not in self.channels:
                        ssl_socket.sendall(f":mock.server 403 {nickname} {channel} :No existe el canal\r\n".encode('utf-8'))
                        continue

                    for user in self.channels[channel]["users"]:
                        if "+i" in self.clients[user]["modes"] and nickname not in self.channels[channel]["users"]:
                            continue  # Ocultar usuarios invisibles a extraños
                        username = self.clients[user].get("username", "~user")
                        flags = "H@ " if user in self.channels[channel]["operators"] else "H"
                        ssl_socket.sendall(
                            f":mock.server 352 {nickname} {channel} {username} {self.host} mock.server {user} {flags} :0 {self.clients[user]['realname']}\r\n".encode('utf-8')
                        )
                    ssl_socket.sendall(f":mock.server 315 {nickname} {channel} :Fin de la lista WHO\r\n".encode('utf-8'))
                    
                elif data.startswith("NAMES"):
                    parts = data.split()
                    channel = parts[1] if len(parts) > 1 else "*"

                    if channel != "*" and channel not in self.channels:
                        ssl_socket.sendall(f":mock.server 403 {nickname} {channel} :No existe el canal\r\n".encode('utf-8'))
                        continue

                    users = []
                    if channel == "*":
                        # Listar todos los usuarios visibles
                        for user in self.clients.values():
                            if "+i" not in user["modes"]:
                                users.append(user["nickname"])
                    else:
                        # Listar usuarios del canal con @ para operadores
                        for user in self.channels[channel]["users"]:
                            prefix = "@" if user in self.channels[channel]["operators"] else ""
                            users.append(f"{prefix}{user}")

                    ssl_socket.sendall(f":mock.server 353 {nickname} = {channel} :{' '.join(users)}\r\n".encode('utf-8'))
                    ssl_socket.sendall(f":mock.server 366 {nickname} {channel} :Fin de la lista NAMES\r\n".encode('utf-8'))
    
                elif data.startswith("REJOIN"):
                    parts = data.split()
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 461 {nickname} REJOIN :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    channel = parts[1]
                    if channel in self.channels and nickname in self.channels[channel]["users"]:
                        # Notificar al usuario
                        ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :Reunión exitosa\r\n".encode('utf-8'))
                    else:
                        ssl_socket.sendall(f":mock.server 442 {nickname} {channel} :No estás en el canal\r\n".encode('utf-8'))
                                        
                elif data.startswith("LIST"):
                    # Enviar lista de canales
                    for channel, details in self.channels.items():
                        topic = details.get("topic", "Sin tema")
                        visible_users = [u for u in details["users"] if "+i" not in self.clients[u]["modes"]]
                        ssl_socket.sendall(
                            f":mock.server 322 {nickname} {channel} {len(visible_users)} :{topic}\r\n".encode('utf-8')
                        )
                    ssl_socket.sendall(f":mock.server 323 {nickname} :Fin de la lista\r\n".encode('utf-8'))
                    
                elif data.startswith("PRIVMSG"):
                    parts = data.split(' ', 2)  # Dividir en 3 partes: PRIVMSG, target, message
                    if len(parts) < 3:
                        ssl_socket.sendall(f":mock.server 461 {nickname} PRIVMSG :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target = parts[1]
                    raw_message = parts[2].strip()

                    # Eliminar el ":" inicial del mensaje si existe (solo el primero)
                    message = raw_message[1:] if raw_message.startswith(":") else raw_message

                    # Obtener username válido (ej. ~user si no está registrado)
                    username = self.clients[nickname].get("username", "~user")

                    # Mensaje a un canal
                    if target.startswith("#"):
                        if target in self.channels:
                            # Formato IRC: :nick!user@host PRIVMSG #canal :mensaje
                            full_message = f":{nickname}!{username}@mock.server PRIVMSG {target} :{message}\r\n"
                            for user in self.channels[target]["users"]:
                                if user != nickname:
                                    self.clients[user]["socket"].sendall(full_message.encode('utf-8'))
                            print(f"[SERVER] Mensaje enviado a canal {target}: {message}")
                        else:
                            ssl_socket.sendall(f":mock.server 403 {nickname} {target} :No existe el canal\r\n".encode('utf-8'))

                    # Mensaje privado a un usuario
                    else:
                        if target in self.clients:
                            # Formato IRC: :nick!user@host PRIVMSG usuario :mensaje
                            full_message = f":{nickname}!{username}@mock.server PRIVMSG {target} :{message}\r\n"
                            self.clients[target]["socket"].sendall(full_message.encode('utf-8'))
                            print(f"[SERVER] Mensaje enviado a usuario {target}: {message}")
                        else:
                            ssl_socket.sendall(f":mock.server 401 {nickname} {target} :El usuario no está conectado\r\n".encode('utf-8'))
                            
                    
                elif data.startswith("NOTICE"):
                    parts = data.split(' ', 2)  # Divide en máximo 3 partes: NOTICE, target, message
                    if len(parts) < 3:
                        ssl_socket.sendall(f":mock.server 461 {nickname} NOTICE :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target = parts[1]
                    message = parts[2][1:] if parts[2].startswith(":") else parts[2]  # Eliminar el ":" inicial si existe

                    if target in self.clients:
                        # Formato IRC estándar: :nickname!username@host NOTICE usuario :mensaje
                        full_message = f":{nickname}!{self.clients[nickname]['username']}@mock.server NOTICE {target} :{message}\r\n"
                        self.clients[target]["socket"].sendall(full_message.encode('utf-8'))
                        print(f"[SERVER] Notificación enviada a {target}: {message}")
                        
                
                elif data.startswith("VERSION"):
                    version_response = (
                        f":mock.server 351 {nickname} mock.irc.server-1.0 mock.server :Python IRC Server\r\n"
                    )
                    ssl_socket.sendall(version_response.encode("utf-8"))
                elif data.startswith("CAP"):
                    # Manejar CAP LS (necesario para clientes modernos)
                    ssl_socket.sendall(b":mock.server CAP * LS :\r\n")
                    
                elif data.startswith("STATS"):
                    parts = data.split()
                    if len(parts) < 2:
                        error_msg = f":mock.server 461 {nickname} STATS :Faltan parámetros\r\n"
                        ssl_socket.sendall(error_msg.encode("utf-8"))
                        continue

                    query = parts[1].upper()
                    if query == "L":  # Ejemplo: Estadísticas de conexiones
                        stats_msg = (
                            f":mock.server 211 {nickname} mock.server :Estadísticas del servidor\r\n"
                            f":mock.server 251 {nickname} :Usuarios conectados: {len(self.clients)}\r\n"
                            f":mock.server 255 {nickname} :Canales activos: {len(self.channels)}\r\n"
                        )
                        ssl_socket.sendall(stats_msg.encode("utf-8"))
                    else:
                        error_msg = f":mock.server 219 {nickname} {query} :Tipo de STATS no soportado\r\n"
                        ssl_socket.sendall(error_msg.encode("utf-8"))

                    end_msg = f":mock.server 219 {nickname} {query} :Fin de STATS\r\n"
                    ssl_socket.sendall(end_msg.encode("utf-8"))
    
                elif data.startswith("PING"):
                    server_name = data.split()[1]
                    ssl_socket.sendall(f"PONG {server_name}\r\n".encode('utf-8'))
                    print(f"[SERVER] PING recibido, PONG enviado a {nickname}")

                elif data.startswith("PONG"):
                    print(f"[SERVER] PONG recibido de {nickname}")
                    if nickname in self.clients:
                        parts = data.split(":", 1)
                        if len(parts) >= 2:
                            received_token = parts[1].strip()
                            stored_token = self.clients[nickname].get("ping_token", "")
                            if received_token == stored_token:
                                self.clients[nickname]["last_pong"] = time.time()
                                print(f"[SERVER] PONG válido de {nickname}")
                            else:
                                print(f"[SERVER] Token inválido de {nickname}")
                                
                elif data.startswith("QUIT"):
                    reason = data.split(":", 1)[1] if ":" in data else "Desconexión voluntaria"
                    print(f"[SERVER] {nickname} se ha desconectado: {reason}")
                    ssl_socket.sendall(f":mock.server 221 {nickname} QUIT :{reason}\r\n".encode('utf-8'))

                    if nickname in self.clients:
                        # Guardar en WHOWAS
                        user_data = {
                            "nickname": nickname,
                            "username": self.clients[nickname].get("username", "~user"),
                            "hostname": addr[0],
                            "realname": self.clients[nickname].get("realname", "Desconocido"),
                            "disconnected_time": time.time()
                        }
                        # Almacenar hasta 10 entradas históricas por usuario
                        if nickname not in self.whowas:
                            self.whowas[nickname] = []
                        self.whowas[nickname].insert(0, user_data)  # Insertar al inicio
                        if len(self.whowas[nickname]) > 10:
                            self.whowas[nickname].pop()  # Mantener solo 10 registros

                    # Eliminar al usuario de todos los canales
                    for channel, details in self.channels.items():
                        if nickname in details["users"]:
                            details["users"].remove(nickname)
                            if not details["users"]:  # Si el canal queda vacío, eliminarlo
                                del self.channels[channel]
                            else:
                                for user in details["users"]:
                                    self.clients[user]["socket"].sendall(f":{nickname} QUIT :{reason}\r\n".encode('utf-8'))
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
