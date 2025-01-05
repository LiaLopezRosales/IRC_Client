import socket
import ssl
from threading import Thread
import time


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

                    # Verificar si el NICK ya está en uso
                    if nickname in self.clients:
                        ssl_socket.sendall(f":mock.server 433 * {nickname} :El apodo ya está en uso\r\n".encode('utf-8'))
                        print(f"[SERVER] NICK rechazado: {nickname} ya está en uso")
                        continue

                    # Registrar el NICK
                    self.clients[nickname] = {
                        "socket": ssl_socket,
                        "modes": [],  # Inicializar la lista de modos del usuario
                        "username": None,
                        "realname": None
                    }
                    ssl_socket.sendall(f":mock.server 001 {nickname} :Bienvenido al servidor\r\n".encode('utf-8'))
                    print(f"[SERVER] Cliente registrado con NICK: {nickname}")

                elif data.startswith("USER"):
                    parts = data.split()
                    if len(parts) < 5:
                        ssl_socket.sendall(f":mock.server 461 * USER :Faltan parámetros\r\n".encode('utf-8'))
                        print("[SERVER] Comando USER rechazado: Faltan parámetros")
                        continue

                    # Verificar si el NICK ya fue registrado
                    if not nickname or nickname not in self.clients:
                        ssl_socket.sendall(f":mock.server 451 * :Debes registrar un NICK antes de usar USER\r\n".encode('utf-8'))
                        print("[SERVER] Comando USER rechazado: NICK no registrado")
                        continue

                    # Completar la información del usuario
                    username = parts[1]
                    realname = " ".join(parts[4:])[1:]  # Combinar el resto como nombre real (sin el prefijo ":")
                    self.clients[nickname]["username"] = username
                    self.clients[nickname]["realname"] = realname

                    ssl_socket.sendall(f":mock.server 002 {nickname} :Usuario registrado correctamente\r\n".encode('utf-8'))
                    print(f"[SERVER] Cliente {nickname} registrado con USER: {username}, Nombre Real: {realname}")

                elif data.startswith("JOIN"):
                # Unirse a un canal
                    channel = data.split()[1]
                    if channel not in self.channels:
                    # Crear canal con el primer usuario como operador
                        self.channels[channel] = {
                                    "users": [nickname],
                                    "operators": [nickname],
                                    "topic": None  # Inicializar el tema del canal
                                }

                        print(f"[SERVER] Canal {channel} creado por {nickname}")
                    else:
                    # Agregar usuario al canal
                        if nickname not in self.channels[channel]["users"]:
                            self.channels[channel]["users"].append(nickname)
                        topic = self.channels[channel].get("topic")
                        if topic:
                            ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :{topic}\r\n".encode('utf-8'))   
                        #ssl_socket.sendall(f":mock.server 331 {nickname} {channel} :Bienvenido al canal {channel}\r\n".encode('utf-8'))
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
                            # Verificar si el modo ya está activado
                            if "+i" not in self.clients[target]["modes"]:
                                self.clients[target]["modes"].append("+i")
                                ssl_socket.sendall(f":mock.server 221 {target} :Modo +i activado\r\n".encode('utf-8'))
                                print(f"[SERVER] {target} ha activado el modo +i (invisible)")
                            else:
                                ssl_socket.sendall(f":mock.server 443 {target} :El modo ya está activado\r\n".encode('utf-8'))
                        elif mode == "-i":
                            # Verificar si el modo está activo para poder desactivarlo
                            if "+i" in self.clients[target]["modes"]:
                                self.clients[target]["modes"].remove("+i")
                                ssl_socket.sendall(f":mock.server 221 {target} :Modo +i desactivado\r\n".encode('utf-8'))
                                print(f"[SERVER] {target} ha desactivado el modo +i (invisible)")
                            else:
                                ssl_socket.sendall(f":mock.server 442 {target} :El modo no estaba activado\r\n".encode('utf-8'))

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
                                    
                                    # Enviar mensaje al usuario que ha sido promovido
                                    if target_user in self.clients:
                                        self.clients[target_user]["socket"].sendall(
                                            f":mock.server MODE {channel} +o {target_user} :Has sido promovido a operador\r\n".encode('utf-8')
                                        )
                                else:
                                    ssl_socket.sendall(f":mock.server 443 {channel} {target_user} :Ya es operador\r\n".encode('utf-8'))
                            else:
                                ssl_socket.sendall(f":mock.server 482 {channel} :No tienes permisos para cambiar modos\r\n".encode('utf-8'))
                        
                        elif mode == "-o":
                            if nickname in self.channels[channel]["operators"]:
                                if target_user in self.channels[channel]["operators"]:
                                    self.channels[channel]["operators"].remove(target_user)
                                    ssl_socket.sendall(f":mock.server 324 {channel} {target_user} :Ya no es operador\r\n".encode('utf-8'))

                                    # Enviar mensaje al usuario que ha perdido el modo operador
                                    if target_user in self.clients:
                                        self.clients[target_user]["socket"].sendall(
                                            f":mock.server MODE {channel} -o {target_user} :Has perdido el modo de operador\r\n".encode('utf-8')
                                        )
                                else:
                                    ssl_socket.sendall(f":mock.server 441 {channel} {target_user} :El usuario no era operador\r\n".encode('utf-8'))
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
                    
                
                elif data.startswith("TOPIC"):
                    parts = data.split(" ", 2)  # Dividir en máximo 3 partes
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
                            ssl_socket.sendall(f":mock.server 331 {nickname} {channel} :No hay un tema establecido para este canal\r\n".encode('utf-8'))
                        continue

                    # Establecimiento o eliminación del tema
                    if len(parts) == 3:
                        if nickname in self.channels[channel]["operators"]:
                            # Manejar eliminar tema si el mensaje es ":"
                            new_topic = parts[2].strip()
                            if new_topic == ":":
                                self.channels[channel]["topic"] = None
                                ssl_socket.sendall(f":mock.server 331 {nickname} {channel} :El tema del canal ha sido eliminado\r\n".encode('utf-8'))
                                print(f"[SERVER] Tema del canal {channel} eliminado por {nickname}")
                            else:
                                # Establecer nuevo tema
                                topic = new_topic[1:] if new_topic.startswith(":") else new_topic
                                self.channels[channel]["topic"] = topic
                                ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :{topic}\r\n".encode('utf-8'))
                                # Notificar al canal sobre el cambio
                                for user in self.channels[channel]["users"]:
                                    self.clients[user]["socket"].sendall(
                                        f":{nickname} TOPIC {channel} :{topic}\r\n".encode('utf-8')
                                    )
                                print(f"[SERVER] Tema del canal {channel} actualizado: {topic}")
                        else:
                            ssl_socket.sendall(f":mock.server 482 {channel} :No tienes permisos para establecer el tema\r\n".encode('utf-8'))

                elif data.startswith("KICK"):
                    parts = data.split(" ", 3)
                    if len(parts) < 3:
                        ssl_socket.sendall(f":mock.server 461 {nickname} KICK :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    channel, target = parts[1], parts[2]
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

                    # Notificar al usuario expulsado
                    try:
                        self.clients[target]["socket"].sendall(
                            f":{nickname} KICK {channel} {target} :{reason}\r\n".encode('utf-8')
                        )
                    except Exception as e:
                        print(f"[SERVER] Error al notificar a {target} sobre su expulsión: {e}")

                    # Eliminar al usuario del canal
                    self.channels[channel]["users"].remove(target)
                    if target in self.channels[channel]["operators"]:
                        self.channels[channel]["operators"].remove(target)

                    # Notificar al operador
                    ssl_socket.sendall(
                        f":mock.server 307 {nickname} {channel} :{target} ha sido expulsado del canal\r\n".encode('utf-8')
                    )

                    # Notificar al resto de los usuarios del canal
                    for user in self.channels[channel]["users"]:
                        if user != nickname:  # No repetir mensaje al operador
                            self.clients[user]["socket"].sendall(
                                f":{nickname} KICK {channel} {target} :{reason}\r\n".encode('utf-8')
                            )

                    # Mensaje de registro en el servidor
                    print(f"[SERVER] {target} fue expulsado del canal {channel} por {nickname}")

                elif data.startswith("INVITE"):
                    parts = data.split()
                    if len(parts) < 3:
                        ssl_socket.sendall(f":mock.server 461 {nickname} INVITE :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target, channel = parts[1], parts[2]

                    if channel not in self.channels:
                        ssl_socket.sendall(f":mock.server 403 {nickname} {channel} :No existe el canal\r\n".encode('utf-8'))
                        continue

                    if target not in self.clients:
                        ssl_socket.sendall(f":mock.server 401 {nickname} {target} :El usuario no está conectado\r\n".encode('utf-8'))
                        continue

                    # Notificar al invitado
                    self.clients[target]["socket"].sendall(f":{nickname} INVITE {target} {channel}\r\n".encode('utf-8'))
                    ssl_socket.sendall(f":mock.server 341 {nickname} {target} {channel} :Invitación enviada\r\n".encode('utf-8'))

                elif data.startswith("WHO"):
                    parts = data.split()
                    channel = parts[1] if len(parts) > 1 else "*"

                    if channel not in self.channels:
                        ssl_socket.sendall(f":mock.server 403 {nickname} {channel} :No existe el canal\r\n".encode('utf-8'))
                        continue

                    for user in self.channels[channel]["users"]:
                        if "+i" in self.clients[user]["modes"] and nickname not in self.channels[channel]["users"]:
                            continue
                        ssl_socket.sendall(f":mock.server 352 {nickname} {channel} {user} :Información del usuario\r\n".encode('utf-8'))

                    ssl_socket.sendall(f":mock.server 315 {nickname} {channel} :Fin de la lista WHO\r\n".encode('utf-8'))

                elif data.startswith("WHOIS"):
                    parts = data.split()
                    if len(parts) < 2:
                        ssl_socket.sendall(f":mock.server 461 {nickname} WHOIS :Faltan parámetros\r\n".encode('utf-8'))
                        continue

                    target = parts[1]
                    if target not in self.clients:
                        ssl_socket.sendall(f":mock.server 401 {nickname} {target} :El usuario no está conectado\r\n".encode('utf-8'))
                        continue

                    ssl_socket.sendall(f":mock.server 311 {nickname} {target} :Información detallada del usuario {target}\r\n".encode('utf-8'))

                elif data.startswith("WHOWAS"):
                    parts = data.split()
                    target = parts[1] if len(parts) > 1 else ""

                    if target not in self.whowas:
                        ssl_socket.sendall(f":mock.server 406 {nickname} {target} :No hay información sobre el usuario\r\n".encode('utf-8'))
                        continue

                    ssl_socket.sendall(f":mock.server 369 {nickname} {target} :Información previa del usuario {target}\r\n".encode('utf-8'))

                elif data.startswith("NAMES"):
                    parts = data.split()
                    channel = parts[1] if len(parts) > 1 else "*"

                    if channel not in self.channels:
                        ssl_socket.sendall(f":mock.server 403 {nickname} {channel} :No existe el canal\r\n".encode('utf-8'))
                        continue

                    # Filtrar usuarios invisibles
                    visible_users = [
                        user for user in self.channels[channel]["users"]
                        if "+i" not in self.clients[user]["modes"] or nickname in self.channels[channel]["users"]
                    ]
                    users = " ".join(visible_users)
                    ssl_socket.sendall(f":mock.server 353 {nickname} {channel} :{users}\r\n".encode('utf-8'))
                    ssl_socket.sendall(f":mock.server 366 {nickname} {channel} :Fin de la lista NAMES\r\n".encode('utf-8'))

                elif data.startswith("REJOIN"):
                    channel = data.split()[1] if len(data.split()) > 1 else ""

                    if channel in self.channels and nickname in self.channels[channel]["users"]:
                        # Simular PART y JOIN
                        self.channels[channel]["users"].remove(nickname)
                        self.channels[channel]["users"].append(nickname)
                        ssl_socket.sendall(f":mock.server 332 {nickname} {channel} :Reunido exitosamente\r\n".encode('utf-8'))

                elif data.startswith("LIST"):
                    # Listar canales
                    if self.channels:
                        for channel, details in self.channels.items():
                            # Verificar si hay usuarios visibles
                            visible_users = [
                                user for user in details["users"]
                                if "+i" not in self.clients[user]["modes"] or nickname in details["users"]
                            ]
                            if not visible_users:
                                continue
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

                    # Guardar en self.whowas
                    if nickname in self.clients:
                        self.whowas[nickname] = {
                            "realname": self.clients[nickname].get("realname", "Desconocido"),
                            "nickname": nickname,
                            "hostname": addr[0],  # Dirección IP del cliente
                            "servername": "mock.server",
                            "disconnected_time": time.strftime("%Y-%m-%d %H:%M:%S")
                        }

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
