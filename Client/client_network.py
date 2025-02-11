# client_network.py

import socket
import threading
import ssl
import time
from Common.irc_protocol import build_message, parse_message
from Common.custom_errors import IRCConnectionError
from Common.custom_errors import ProtocolError
#import re
response_patterns = {
    "ERROR": {
        "401": "No existe canal/nickname",
        "402": "No existe el servidor",
        "403": "No existe el canal",
        "404": "No puedes enviar al canal",
        "405": "Te has unido a demasiados canales",
        "406": "No existió el nickname",
        "407": "Demasiados objetivos",
        "408": "No existe el servicio",
        "421": "Comando desconocido",
        "422": "No se pudo abrir archivo MOTD/No hay MOTD",
        "423": "No hay información administrativa",
        "431": "Falta nickname",
        "432": "Nickname inválido",
        "433": "Nickname ya está en uso",
        "437": "Nickname/canal no disponible temporalmente",
        "441": "El usuario objetivo no está en el canal",
        "442": "No estás en el canal",
        "443": "El usuario ya pertenece al canal",
        "444": "Usuario no logeado",
        "445": "Servidor no soporta SUMMON",
        "446": "Servidor no soporta USERS",
        "461": "Faltan parámetros",
        "462": "Ya registrado",
        "464": "Contraseña incorrecta",
        "465": "Exiliado del servidor",
        "471": "No puedes unirte al canal(canal lleno)",
        "473": "No puedes unirte al canal(solo con invitación)",
        "474": "No puedes unirte al canal(exiliado del canal)",
        "475": "No puedes unirte al canal(+k)",
        "476": "Nombre de canal inválido",
        "477": "El canal no soporta modos",
        "482": "No tienes permiso para realizar esta acción",
        "481": "Necesitas privilegios de operador",
        "483": "No puedes matar un servidor",
        "484": "Conexión restringida",
        "485": "No eres el operador original del canal",
        "491": "Credenciales incorrectas",
        "501": "Modo no reconocido",
        "502": "No puedes cambiar el modo de otro usuario(fuera de un canal)"
    }
}
expected_codes = {
    "/whois": [r" 311 ", r" 312 ", r" 317 ", r" 319 "],  # Todos los códigos que pueden aparecer en WHOIS
    "/whowas": [r" 314 ", r" 312 "],  # Todos los códigos para WHOWAS
    "/admin": [r"256" , r"257", r"258" , r"259"],
    "/motd": [r"375" , r"372", r"376"],
    "/lusers": [r"251" , r"252", r"253" , r"254", r"255" , r"265", r"266"],
    "/stats": [r"211" , r"212", r"219" , r"249"],
    "/trace": [r"200" , r"201", r"202" , r"203", r"204" , r"205", r"206", r"208" , r"261", r"262"],
    "/users": [r"392" , r"393", r"394" , r"395"],
}


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
        self.is_connected = False
        self.expected_response = None  # Respuesta esperada para el comando actual
        self.response_received = threading.Event()  # Evento para sincronizar
        self.last_matching_response = None
        self.multi_response_buffer = []  # Nuevo buffer para respuestas multiparte
        self.response_terminator = None  # Patrón que indica fin de respuesta múltiple
        self.command = None
        
    def set_expected_response(self, command, pattern, terminator=None):
        """Define el patrón de la respuesta que se espera recibir."""
        if command == "/topic":
            self.command = command
            self.expected_response = pattern if isinstance(pattern, tuple) else (pattern,)
            self.response_terminator = terminator
            self.multi_response_buffer = []
            self.response_received.clear()
        else:
            self.command = command
            self.expected_response = pattern
            self.response_terminator = terminator 
            self.multi_response_buffer = []
            self.response_received.clear()  # Reinicia el evento

    def wait_for_response(self, timeout=5):
        """Espera hasta recibir una respuesta que coincida con el patrón."""
        if self.response_received.wait(timeout=timeout):
            if self.response_terminator:
                return self.multi_response_buffer if self.multi_response_buffer else []
            return [self.last_matching_response] if self.last_matching_response else []
        
        return [] 

    def connect_client(self,password,nick,real_name, retries=3, delay=2):
        for attempt in range(retries):
            try:
                self.ssl_socket = socket.create_connection((self.host, self.port))
                self.pass_command(password)
                self.nick(nick)
                self.set_user(nick, real_name)
                self.is_connected = True
                return
            except Exception as e:
                if attempt < retries - 1:
                    print(f"Reintentando conexión ({attempt + 1}/{retries})...")
                    time.sleep(delay)
                else:
                    self.is_connected = False
                    raise IRCConnectionError(f"Error al conectar después de {retries} intentos: {e}")
                
    def send(self, command, params=None, trailing=None):
        """
        Envía un mensaje al servidor en formato IRC.
        """
        try:
            message = build_message(command, params, trailing)
            # print(f"Enviando mensaje: {message}")
            self.ssl_socket.sendall(message.encode('utf-8') + b'\r\n')
        
        except Exception as e:
            raise IRCConnectionError(f"Error al enviar mensaje: {e}")

    def receive(self, message_queue=None):
        """
        Recibe y procesa mensajes del servidor en tiempo real.
        Responde automáticamente a PING.

        Args:
            message_queue (queue.Queue, optional): Cola para enviar mensajes a la interfaz gráfica.
                                                Si es None, los mensajes se imprimen en la consola.
        """
        try:
            while self.is_connected:
                # Leer datos del servidor
                data = self.ssl_socket.recv(4096).decode('utf-8').strip()
                if not data:
                    break

                # Dividir los mensajes en líneas por el delimitador IRC (\r\n)
                responses = data.split('\r\n')

                # Procesar cada línea
                for line in responses:
                    if line.startswith("PING"):
                        # Responder automáticamente a PING con PONG
                        server_name = line.split()[1]
                        # print(f"[CLIENTE] PING recibido desde {server_name}. Respondiendo con PONG.")
                        self.pong(server_name)
                    else:
                        parts = line.split()
                        if len(parts) > 1 and parts[1].isdigit():
                            error_code = parts[1]
                            if error_code in response_patterns["ERROR"]:
                                self.last_matching_response = line
                                self.response_received.set()  # Notificar a `wait_for_response()`
                                continue  # No seguir procesando este mensaje
                            
                        # Manejar mensajes espontáneos (PRIVMSG, NOTICE, etc.)
                        if "PRIVMSG" in line or "NOTICE" in line:
                            sender = line.split('!')[0][1:]  # Obtener el remitente
                            msg_content = line.split(":", 2)[-1]  # Obtener el mensaje
                            print(f"\n[{sender}] {msg_content}")  # Mostrar el mensaje directamente
                            if message_queue:
                                message_queue.put(line)
                            continue  # No procesar como respuesta esperada
                        
                        # Detectar si alguien se une a un canal (JOIN)
                        if " JOIN " in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                user = line.split("!")[0][1:]  # Extrae el nombre de usuario
                                channel = parts[-1]  # Canal al que se unió
                                print(f"\n🔹 {user} se ha unido a {channel}")
                            if message_queue:
                                message_queue.put(line)
                            continue

                        # Detectar si alguien sale de un canal (PART)
                        if " PART " in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                user = line.split("!")[0][1:]  # Extrae el nombre de usuario
                                channel = parts[2]  # Canal del que salió
                                reason = " ".join(parts[3:]).lstrip(":") if len(parts) > 3 else ""
                                print(f"\n🔸 {user} ha salido de {channel} ({reason})")
                            if message_queue:
                                message_queue.put(line)
                            continue

                        # Detectar si alguien es expulsado (KICK)
                        if " KICK " in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                kicker = line.split("!")[0][1:]  # Quién ejecutó la acción
                                channel = parts[2]  # Canal donde ocurrió el kick
                                kicked_user = parts[3]  # Usuario expulsado
                                reason = " ".join(parts[4:]).lstrip(":") if len(parts) > 4 else ""
                                print(f"\n❌ {kicked_user} fue expulsado de {channel} por {kicker} ({reason})")
                            if message_queue:
                                message_queue.put(line)
                            continue

                        # Detectar si el usuario fue invitado a un canal (INVITE)
                        if " INVITE " in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                inviter = line.split("!")[0][1:]  # Quién envió la invitación
                                invited_user = parts[2]  # Usuario invitado
                                channel = parts[-1].lstrip(":")  # Canal al que fue invitado
                                print(f"\n📩 {inviter} ha invitado a {invited_user} a {channel}")
                            if message_queue:
                                message_queue.put(line)
                            continue

                        if self.command == "/topic":
                            if any(code in line for code in self.expected_response):
                                self.multi_response_buffer.append(line)

                                # Si no hay terminador, es una respuesta de una sola línea y se almacena
                                if not self.response_terminator:
                                    self.last_matching_response = line
                                    self.response_received.set()
                                    continue
                                if message_queue:
                                    message_queue.put(line)
                        else:

                            # Manejar respuestas esperadas
                            if self.command in expected_codes:
                                if any(code in line for code in expected_codes[self.command]):
                                    self.multi_response_buffer.append(line)
                                if self.response_terminator and self.response_terminator in line:
                                    self.response_received.set()
                            else:
                                if self.expected_response and self.expected_response in line:
                                    self.multi_response_buffer.append(line)  # Almacenar la línea correctamente

                                    # Si no hay terminador, significa que es una respuesta de una sola línea
                                    if not self.response_terminator:
                                        self.last_matching_response = line
                                        self.response_received.set()
                                        continue

                                # Si llega el terminador (`366` para /NAMES, `315` para /WHO), finaliza la respuesta múltiple
                                if self.response_terminator and self.response_terminator in line:
                                    self.response_received.set()


                        if message_queue:
                            message_queue.put(line)
                        # else:
                        #     print(line)  # Opcional: imprime todos los mensajes (para depuración)
        except Exception as e:
            print(f"Error al recibir mensaje: {e}")
            self.close()

    def join_channel(self, channel):
        """
        Envía un comando JOIN para unirse a un canal.
        
        Args:
            channel (str): Nombre del canal (e.g., "#general").
        """
        self.send("JOIN", [channel])

    def change_topic(self, channel, new_topic=None):
        """
        Envía un comando TOPIC para consultar o cambiar el tema de un canal.

        Args:
            channel (str): Nombre del canal (e.g., "#general").
            new_topic (str, optional): Nuevo tema. Si es None o "", se consulta el tema actual.
        """
        if new_topic:  # Cambiar el tema
            self.send("TOPIC", [channel], new_topic)
        else:  # Consultar el tema
            self.send("TOPIC", [channel])

    def change_mode(self, target, mode, params=None):
        """
        Cambia el modo de un canal o usuario.

        Args:
            target (str): Destinatario (usuario o canal).
            mode (str): Modo a establecer.
            params (str, optional): Parámetros adicionales para ciertos modos.
        """
        if params:
            self.send("MODE", [target, mode, params])
        else:
            self.send("MODE", [target, mode])

    def message(self, target, message):
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

    def notice(self, target, message):
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

    def close(self):
        if self.is_connected:
            try:
                self.is_connected = False
                if self.ssl_socket:
                    try:
                        self.ssl_socket.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass  # El socket ya estaba cerrado
                    self.ssl_socket.close()
            except Exception as e:
                print(f"Error al cerrar: {e}")




    def oper(self, name, password, privileges=None):
        """
        Otorga privilegios de operador a un usuario.

        Args:
            name (str): Nombre del usuario que se desea otorgar privilegios.
            password (str): Contraseña para la autenticación del operador.
            privileges (list, optional): Lista de privilegios adicionales a otorgar.
        """
        params = [name, password]
        if privileges:
            params.extend(privileges)
        self.send("OPER", params)

    def kick(self, channel, user, reason="Expulsado"): 
        """
        Expulsa a un usuario de un canal especificado.

        Args:
            channel (str): Canal del cual expulsar al usuario.
            user (str): Nombre del usuario a expulsar.
            reason (str, optional): Motivo de la expulsión. Default es "Expulsado".
        """
        self.send("KICK", [channel, user], reason)

    def invite(self, user, channel):
        """
        Invita a un usuario a un canal específico.

        Args:
            user (str): Nombre del usuario a invitar.
            channel (str): Canal al que se invita al usuario.
        """
        self.send("INVITE", [user, channel])

    def names(self, channel):
        """
        Solicita la lista de usuarios presentes en un canal.

        Args:
            channel (str): Canal del cual listar los usuarios.
        """
        self.send("NAMES", [channel])

    def list(self):
        """
        Solicita la lista de canales disponibles en el servidor.
        """
        self.send("LIST")

    def who(self, mask):
        """
        Solicita información sobre usuarios coincidentes con un criterio.

        Args:
            mask (str): Máscara de búsqueda para filtrar usuarios.
        """
        self.send("WHO", [mask])

    def whois(self, user):
        """
        Solicita información detallada sobre un usuario específico.

        Args:
            user (str): Nombre del usuario a consultar.
        """
        self.send("WHOIS", [user])

    def whowas(self, user):
        """
        Solicita información sobre un usuario previamente conectado.

        Args:
            user (str): Nombre del usuario previamente conectado.
        """
        self.send("WHOWAS", [user])

    def admin(self):
        """
        Solicita información del administrador del servidor.
        """
        self.send("ADMIN")

    def info(self):
        """
        Solicita información general sobre el servidor.
        """
        self.send("INFO")

    def version(self):
        """
        Solicita la versión del software del servidor.
        """
        self.send("VERSION")

    def stats(self,argument):
        """
        Solicita estadísticas del servidor.
        """
        self.send("STATS", [argument])

    def links(self):
        """
        Solicita una lista de servidores conectados.
        """
        self.send("LINKS")

    def time(self):
        """
        Solicita la hora actual del servidor.
        """
        self.send("TIME")

    def connect_servers(self, target_server, port):
        """
        Solicita la conexión a otro servidor a través del servidor actual.

        Args:
            target_server (str): Nombre del servidor al que conectarse.
            port (int): Puerto del servidor de destino.
        """
        self.send("CONNECT", [target_server, str(port)])

    def trace(self):
        """
        Solicita la traza de la ruta de conexión hasta el servidor.
        """
        self.send("TRACE")

    def away(self, message="Ausente"): 
        """
        Establece un mensaje de ausencia para el usuario.

        Args:
            message (str, optional): Mensaje de ausencia. Default es "Ausente".
        """
        self.send("AWAY", trailing=message)

    def rehash(self):
        """
        Solicita la recarga de la configuración del servidor.
        """
        self.send("REHASH")

    def die(self):
        """
        Solicita la terminación del servidor (solo operadores).
        """
        self.send("DIE")

    def restart(self):
        """
        Solicita el reinicio del servidor.
        """
        self.send("RESTART")

    def pass_command(self, password):
        """
        Envía el comando PASS para establecer la contraseña de conexión.

        Args:
            password (str): Contraseña para la conexión.
        """
        self.send("PASS", [password])

    def nick(self, nickname):
        """
        Envía el comando NICK para establecer o cambiar el apodo del cliente.

        Args:
            nickname (str): Apodo deseado para el cliente.
        """
        self.send("NICK", [nickname])

    def service(self, nickname, reserved, distribution, type_, reserved_2, info):
        """
        Envía el comando SERVICE para registrar un nuevo servicio.

        Args:
            nickname (str): Nombre del servicio.
            reserved (str): Campo reservado (actualmente no utilizado).
            distribution (str): Distribución del servicio (alcance).
            type_ (str): Tipo del servicio (reservado para futuro uso).
            reserved_2 (str): Segundo campo reservado (no utilizado).
            info (str): Información adicional del servicio.
        """
        self.send("SERVICE", [nickname, reserved, distribution, type_, reserved_2], info)

    def squit(self, server, comment):
        """
        Envía el comando SQUIT para desconectar un servidor remoto (solo operadores).

        Args:
            server (str): Nombre del servidor a desconectar.
            comment (str): Razón de la desconexión.
        """
        self.send("SQUIT", [server], comment)

    def motd(self, target=None):
        """
        Envía el comando MOTD para obtener el "Message of the Day" de un servidor.

        Args:
            target (str, optional): Servidor del cual obtener el MOTD.
        """
        if target:
            self.send("MOTD", [target])
        else:
            self.send("MOTD")

    def lusers(self, mask=None, target=None):
        """
        Envía el comando LUSERS para obtener estadísticas del tamaño de la red IRC.

        Args:
            mask (str, optional): Máscara para filtrar servidores.
            target (str, optional): Servidor objetivo para la consulta.
        """
        params = []
        if mask:
            params.append(mask)
        if target:
            params.append(target)
        self.send("LUSERS", params)

    def servlist(self, mask=None, type_=None):
        """
        Envía el comando SERVLIST para listar servicios disponibles.

        Args:
            mask (str, optional): Máscara para filtrar servicios.
            type_ (str, optional): Tipo de servicio para filtrar.
        """
        params = []
        if mask:
            params.append(mask)
        if type_:
            params.append(type_)
        self.send("SERVLIST", params)

    def squery(self, servicename, text):
        """
        Envía el comando SQUERY para enviar un mensaje a un servicio.

        Args:
            servicename (str): Nombre del servicio objetivo.
            text (str): Mensaje a enviar al servicio.
        """
        self.send("SQUERY", [servicename], text)
        
    def kill(self, target, comment):
        """
        Expulsa a un usuario de la red IRC (requiere privilegios de operador).

        Args:
            target (str): Nombre del usuario a expulsar.
            comment (str): Razón para expulsar al usuario.
        """
        self.send("KILL", [target], comment)

    def error(self, message):
        """
        Envía un mensaje de error al cliente desde el servidor.

        Args:
            message (str): Mensaje de error a enviar.
        """
        self.send("ERROR", trailing=message)

    def summon(self, user, target_server=None):
        """
        Solicita a un servidor IRC que intente notificar a un usuario conectado al sistema local.

        Args:
            user (str): Nombre del usuario que se intentará contactar.
            target_server (str, optional): Servidor objetivo para enviar la solicitud.
        """
        params = [user]
        if target_server:
            params.append(target_server)
        self.send("SUMMON", params)

    def users(self, target_server=None):
        """
        Solicita la lista de usuarios conectados al servidor.

        Args:
            target_server (str, optional): Servidor del cual solicitar la lista de usuarios.
        """
        if target_server:
            self.send("USERS", [target_server])
        else:
            self.send("USERS")

    def operwall(self, message):
        """
        Envía un mensaje global a todos los operadores de la red.

        Args:
            message (str): Mensaje a enviar.
        """
        self.send("WALLOPS", trailing=message)

    def userhost(self, *nicks):
        """
        Solicita información sobre uno o más apodos en la red.

        Args:
            nicks (str): Uno o más apodos a consultar.
        """
        self.send("USERHOST", list(nicks))

    def ison(self, *nicks):
        """
        Verifica si uno o más apodos están conectados.

        Args:
            nicks (str): Uno o más apodos a verificar.
        """
        self.send("ISON", list(nicks))
