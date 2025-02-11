import threading
from client_network import ClientConnection
from Common.shared_constants import DEFAULT_HOST, DEFAULT_PORT
from Common.custom_errors import IRCConnectionError
import time

def start_receiver_thread(connection):
    """
    Inicia un hilo para recibir mensajes del servidor en tiempo real.
    """
    def receiver():
        try:
            connection.receive()
        except Exception as e:
            print(f"Error en el hilo de recepción: {e}")

    thread = threading.Thread(target=receiver)
    thread.daemon = True  # El hilo se cerrará cuando el programa principal termine
    thread.start()

def execute_command(connection, command, argument, nick):
    """
    Ejecuta un comando específico en la conexión IRC.
    """
    response_patterns = {
    "/nick": r" NICK ",
    "/join": r" JOIN ",
    "/part": r" PART ",
    "/privmsg": r" PRIVMSG ",
    "/notice": r" NOTICE ",
    "/quit": "ERROR :Closing link",
    "/mode": r" MODE ",
    "/topic": (r" TOPIC ", r" 331 ", r" 332 "),
    "/names": (r' 353 ', r' 366 '),
    "/list": (r' 322 ', r' 323 '),
    "/invite": r" INVITE ",
    "/kick": r" KICK ",
    "/who": (r' 352 ', r' 315 '),
    "/whois": (r' 311 ', r' 318 '),  
    "/whowas": (r' 314 ', r' 369 '), 
    "/oper": r" 381 ",
    "/kill": r" KILL ",
    "/wallops": r" WALLOPS ",
    "/version": r" 351 ",
    "/stats": r" 248 ",
    "/links": (r' 364 ', r' 365 '),
    "/time": r" 391 ",
    "/admin": (r' 256 ', r' 259 '),
    "/info": (r' 371 ', r' 374 '),
    "/trace": r" 200 ",
    "/connect": r" CONNECT ",
    "/squit": r" SQUIT ",
    "/ping": r" PONG ",
    "/pong": r" PING ",
    "/away": r" 306 ",
    "/rehash": r" REHASH ",
    "/die": r" DIE ",
    "/restart": r" RESTART ",
    "/userhost": r" 302 ",
    "/ison": r" 303 ",
    "/service": r" 383 ",
    "/motd": (r' 375 ', r' 376 '),
    "/lusers": (r' 251 ', r' 266 '),
    "/servlist": (r' 234 ', r' 235 '),
    "/squery": r" SQUERY ",
    "/summon": r" 342 ",
    "/users": (r' 392 ', r' 395 '),
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


    try:
        if command == "/topic":
            patterns = (r" TOPIC ", r" 331 ", r" 332 ")  # Capturar cambios y consultas de topic
            connection.set_expected_response(command, patterns, None)
        elif command in ["/list", "/names", "/who", "/whois", "/whowas", "/motd", "/lusers", "/servlist", "/users", "/links", "/admin", "/info"]:
            pattern, terminator = response_patterns[command]
            connection.set_expected_response(command, pattern, terminator)
        elif command in response_patterns:
            connection.set_expected_response(command, response_patterns[command])
        else:
            connection.set_expected_response(command, None)
            
        if command == "/nick":
            connection.nick(argument)
        elif command == "/join":
            connection.join_channel(argument)
        elif command == "/part":
            connection.part_channel(argument)
        elif command == "/notice":
            try:
                target, message = argument.split(" ", 1)
                connection.notice(target, message)
            except ValueError:
                print("Faltan parámetros")
                return True

        elif command == "/quit":
            connection.quit(argument)
            #return False  # Indica que el cliente debe cerrarse
        elif command == "/privmsg":
            try:
                target, message = argument.split(" ", 1)
                connection.message(target, message)
            except ValueError:
                print("Faltan parámetros")
                return True

        elif command == "/mode":
            try:
                target, mode = argument.split(" ", 1)
                connection.change_mode(target, mode)
            except ValueError:
                print("Faltan parámetros")
                return True
        elif command == "/topic":
            # Separa el canal y el tema (si existe)
            try:
                channel, new_topic = argument.split(" ", 1)
                connection.change_topic(channel, new_topic)
            except ValueError:
                # Si no hay tema, consulta el existente
                if argument:
                    connection.change_topic(argument)
                else:
                    print("Faltan parámetros")
                    return True


        elif command == "/names":
            connection.names(argument)
        elif command == "/list":
            connection.list()
        elif command == "/invite":
            try:
                user, channel = argument.split(" ", 1)
                connection.invite(user, channel)
            except ValueError:
                print("Faltan parámetros")
                return True
        elif command == "/kick":
            try:
                channel, user = argument.split(" ", 1)
                connection.kick(channel, user)
            except ValueError:
                print("Faltan parámetros")
                return True

        elif command == "/who":
            connection.who(argument)
        elif command == "/whois":
            connection.whois(argument)
        elif command == "/whowas":
            connection.whowas(argument)
        elif command == "/oper":
            try:
                name, password = argument.split(" ", 1)
                connection.oper(name, password)
            except ValueError:
                print("Faltan parámetros")
                return True
        elif command == "/kill":
            try:
                target, comment = argument.split(" ", 1)
                connection.kill(target, comment)
            except ValueError:
                print("Faltan parámetros")
                return True

        elif command == "/operwall":
            connection.operwall(argument)
        elif command == "/version":
            connection.version()
        elif command == "/stats":
            connection.stats(argument)
        elif command == "/links":
            connection.links()
        elif command == "/time":
            connection.time()
        elif command == "/admin":
            connection.admin()
        elif command == "/info":
            connection.info()
        elif command == "/trace":
            connection.trace()
        elif command == "/connect":
            try:
                target_server, port = argument.split(" ", 1)
                connection.connect_servers(target_server, port)
            except ValueError:
                print("Faltan parámetros")
                return True

        elif command == "/squit":
            try:
                server, comment = argument.split(" ", 1)
                connection.squit(server, comment)
            except ValueError:
                print("Faltan parámetros")
                return True

        elif command == "/ping":
            connection.ping(argument)
        elif command == "/pong":
            connection.pong(argument)
        elif command == "/away":
            connection.away(argument)
        elif command == "/rehash":
            connection.rehash()
        elif command == "/die":
            connection.die()
        elif command == "/restart":
            connection.restart()
        elif command == "/userhost":
            connection.userhost(argument)
        elif command == "/ison":
            connection.ison(argument)
        elif command == "/service":
            try:
                parts = argument.split(" ", 5)
                if len(parts) != 6:
                    print("Error: Formato: /service nickname reserved distribution tipo reserved_2 info")
                    return True
                nickname, reserved, distribution, tipo, reserved_2, info = parts
                connection.service(nickname, reserved, distribution, tipo, reserved_2, info)
            except Exception as e:
                print(f"Error en /service: {e}")

        elif command == "/motd":
            target = argument if argument else None
            connection.motd(target)

        elif command == "/lusers":
            parts = argument.split(" ", 1)
            mask = parts[0] if parts else None
            target = parts[1] if len(parts) > 1 else None
            connection.lusers(mask, target)

        elif command == "/servlist":
            parts = argument.split(" ", 1)
            mask = parts[0] if parts else None
            type_ = parts[1] if len(parts) > 1 else None
            connection.servlist(mask, type_)

        elif command == "/squery":
            if not argument:
                print("Error: Formato: /squery servicename mensaje")
                return True
            parts = argument.split(" ", 1)
            if len(parts) < 2:
                print("Error: Falta el mensaje")
                return True
            servicename, text = parts
            connection.squery(servicename, text)

        elif command == "/summon":
            if not argument:
                print("Error: Formato: /summon usuario [servidor]")
                return True
            parts = argument.split(" ", 1)
            user = parts[0]
            target_server = parts[1] if len(parts) > 1 else None
            connection.summon(user, target_server)

        elif command == "/users":
            target_server = argument if argument else None
            connection.users(target_server)
        else:
            print(f"Comando no reconocido: {command}")
            return True  # Continúa en modo interactivo
        
        # Espera la respuesta específica del servidor (ignora otros mensajes)
        response = connection.wait_for_response(timeout=4)
        if not response and command=="/quit":
                # Si no se recibió respuesta, asume que la desconexión fue exitosa
                response = "Desconectado del servidor"

        # Formatea la respuesta según el test
        formatted_response = format_response(command, argument, nick, response)
        # print(formatted_response if formatted_response else "Sin respuesta del servidor")
        if format_response:
            if isinstance(formatted_response, list):
                for msg in formatted_response:
                    print(msg)
            else:
                print(formatted_response)
        else:
            print(f"Sin respuesta del servidor")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False
    
def format_response(command, argument, nick, server_response):
    """Convierte la respuesta del servidor al formato esperado por el test."""
    #print(argument)
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
    if isinstance(server_response, list) and len(server_response)==1:
        server_response = " ".join(server_response)

    error_messages = response_patterns.get("ERROR", {})
    formatted = []
    #print(f"server {server_response}")
    if isinstance(server_response, str):
        parts = server_response.split()
        if len(parts) > 1 and parts[1].isdigit() and parts[1] in response_patterns["ERROR"]:
            return response_patterns["ERROR"][parts[1]]
        
    if command == "/time":
        if server_response:
            parts = server_response.split(":", 2)  # Dividir en tres partes para capturar bien la fecha y hora
            if len(parts) > 2:
                time = f"Hora del servidor: {parts[2].strip()}"
    else:
        time = "No disponible"        
    
    if command == "/topic":
        formatted = []
        if isinstance(server_response, str):  
            server_response = server_response.split("\r\n")

        for response in server_response:
            parts = response.split()
            if len(parts) < 2:
                continue

            # Respuesta 331: No hay tema establecido
            if "331" in parts[1]:
                channel = parts[3]
                formatted.append(f"El canal {channel} no tiene tema establecido.")

            # Respuesta 332: Tema actual del canal
            elif "332" in parts[1]:
                channel = parts[3]
                topic = " ".join(parts[4:]).lstrip(":")
                formatted.append(f"Tema de {channel}: {topic}")

            # Comando TOPIC de un usuario (cambio de tema)
            elif "TOPIC" in parts[1] and "!" in response:
                user = parts[0].split("!")[0][1:]
                channel = parts[2]
                new_topic = " ".join(parts[3:]).lstrip(":")
                formatted.append(f"{user} ha cambiado el tema de {channel} a: {new_topic}")

        return "\n".join(formatted) if formatted else "No se recibió respuesta del servidor."

    
    for response in server_response or []:
        parts = response.split()
        # print(response)
        
        # Detectar errores (solo si la respuesta tiene un código numérico)
        if len(parts) > 1 and parts[1].isdigit() and parts[1] in error_messages:
            # print(f"3")
            return error_messages[parts[1]]
        
        # Formatear respuestas multiparte
        elif command == "/list":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")  # Asegurar que se divida en líneas correctamente

            for response in server_response:
                #print(f"Procesando línea de LIST: {response}")  # Depuración
                if " 322 " in response:
                    parts = response.split()
                    if len(parts) >= 6:
                        channel = parts[3]
                        users = parts[4]
                        topic = " ".join(parts[5:]).lstrip(":")  # Eliminar `:` al inicio del tema
                        formatted.append(f"Canal: {channel} - Usuarios: {users} - Tema/Modo: {topic}")

            return "\n".join(formatted) if formatted else "No se encontraron canales."

        elif command == "/info":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")  # Asegurar que se divida en líneas correctamente
                
            for response in server_response:
                if " 371 " in response:
                        formatted.append(response)

            return "\n".join(formatted) if formatted else "No se encontraron canales."
        elif command == "/names":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\n")
            for response in server_response:
                #print(f"Procesando línea de NAMES: {response}")  # Depuración
                if " 353 " in response:  # Mensaje de nombres en el canal
                    parts = response.split(":", 2)  # Divide en tres partes para asegurarse de capturar bien los nombres
                    if len(parts) > 2:
                        users = parts[2].strip()  # Extrae los nombres de usuario correctamente
                        formatted.append(users)
            return f"Usuarios en {argument}: {' '.join(formatted)}" if formatted else "No se encontraron usuarios."


        elif command == "/who":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")  # Convertirlo en lista si es necesario

            for response in server_response:
                #print(f"Procesando línea de WHO: {response}")  # Depuración
                if " 352 " in response:
                    parts = response.split()
                    if len(parts) >= 10:
                        username = parts[7]
                        channel = parts[3]
                        ip = parts[4]
                        real_name = " ".join(parts[9:])  # Captura el nombre real al final
                        formatted.append(f"Usuario: {username} - Canal: {channel} - IP: {ip} - Nombre: {real_name}")

            return "\n".join(formatted) if formatted else "No se encontraron usuarios."


        elif command == "/whois":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")  # Asegurar que se divida correctamente

            for response in server_response:
                #print(f"Procesando línea de WHOIS: {response}")  # Depuración
                parts = response.split()
                if len(parts) >= 5:
                    if "311" in parts[1]:  # Información del usuario
                        formatted.append(f"Información de {parts[3]}: Usuario real: {parts[4]} - Host: {parts[5]}")
                    elif "312" in parts[1]:  # Servidor en el que está
                        formatted.append(f"Servidor de {parts[3]}: {parts[4]} - {parts[5]}")
                    elif "317" in parts[1]:  # Tiempo inactivo
                        formatted.append(f"{parts[3]} ha estado inactivo por {parts[4]} segundos")
                    elif "319" in parts[1]:  # Canales a los que pertenece
                        formatted.append(f"Canales de {parts[3]}: {' '.join(parts[4:])}")

            return "\n".join(formatted) if formatted else f"No se encontró información de {argument}."

        
        elif command == "/whowas":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")

            for response in server_response:
                #print(f"Procesando línea de WHOWAS: {response}")  # Depuración
                parts = response.split()
                if len(parts) >= 5:
                    if "314" in parts[1]:  # Información del usuario desconectado
                        formatted.append(f"Historial de {parts[3]}: Usuario real: {parts[4]} - Host: {parts[5]}")
                    elif "312" in parts[1]:  # Último servidor donde estuvo conectado
                        formatted.append(f"Último servidor de {parts[3]}: {parts[4]} - {parts[5]} {parts[6]} {parts[7]} {parts[8]} {parts[9]}")
                    elif "369" in parts[1]:  # Fin de la lista WHOWAS
                        formatted.append(f"Fin del historial de {parts[3]}.")

            return "\n".join(formatted) if formatted else f"No hay historial de {argument} disponible."
        
        elif command == "/links":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")

            for response in server_response:
                #print(f"Procesando línea de LINKS: {response}")  # Depuración
                parts = response.split()
                if len(parts) >= 6 and "364" in parts[1]:  # Verifica que sea una línea válida
                    server_name = parts[3]
                    host = parts[4]
                    info = " ".join(parts[5:]).lstrip(":")
                    formatted.append(f"Servidor: {server_name} - Host: {host} - Info: {info}")

            return "\n".join(formatted) if formatted else "No hay servidores conectados."
        
        elif command == "/admin":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")

            for response in server_response:
                #print(f"Procesando línea de ADMIN: {response}")  # Depuración
                parts = response.split(":", 1)  # Separa por `:` para extraer la información
                if len(parts) > 1:
                    formatted.append(parts[1].strip())  # Guarda solo la parte importante

            return "\n".join(formatted) if formatted else "No hay información de administración."
        
        elif command == "/motd":
            formatted = []
            if isinstance(server_response, str):
                server_response = server_response.split("\r\n")

            is_motd = False  # Bandera para saber cuándo empezar a capturar
            for response in server_response:
                #print(f"Procesando línea de MOTD: {response}")  # Depuración
                parts = response.split(":", 2)  # Divide en tres partes para asegurar la captura del mensaje

                # Detectar inicio del MOTD
                if "375" in response:
                    is_motd = True  # Se activa la captura de mensaje
                    formatted.append("Mensaje del día:")
                    continue  # No queremos agregar la línea `375`

                # Capturar líneas del MOTD (`372`)
                if is_motd and "372" in response:
                    if len(parts) > 2:
                        formatted.append(parts[2].strip())  # Agregar la parte que contiene el mensaje real

                # Detectar final del MOTD (`376`) y detener la captura
                if "376" in response:
                    formatted.append("Fin del mensaje del día.")  
                    break  # Salimos del bucle, ya no necesitamos seguir procesando

            return "\n".join(formatted) if formatted else "No hay mensaje del día."
        
        
        elif command == "/lusers":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")

            for response in server_response:
                #print(f"Procesando línea de LUSERS: {response}")  # Depuración
                parts = response.split(":", 1)  # Separa por `:` para extraer la información
                if len(parts) > 1:
                    formatted.append(parts[1].strip())

            return "Estadísticas del servidor:\n" + "\n".join(formatted) if formatted else "No hay información de usuarios."
        
        elif command == "/servlist":
            formatted = []
            if isinstance(server_response, str):  
                server_response = server_response.split("\r\n")

            for response in server_response:
                #print(f"Procesando línea de SERVLIST: {response}")  # Depuración
                parts = response.split()
                if len(parts) >= 6 and "234" in parts[1]:  # Verifica que sea una línea válida
                    service_name = parts[3]
                    description = " ".join(parts[4:]).lstrip(":")
                    formatted.append(f"Servicio: {service_name} - Descripción: {description}")

            return "\n".join(formatted) if formatted else "No hay servicios disponibles."
                
    mapping = {
        "/nick": f"Tu nuevo apodo es {argument}",
        "/join": f"Te has unido al canal {argument}",
        "/part": f"Has salido del canal {argument}",
        "/privmsg": f"Mensaje enviado: {argument}",
        "/notice": f"Notificacion de {nick}: {argument}",
        "/quit": "Desconectado del servidor",
        "/mode": f"Modo cambiado en {argument.split()[0] if argument else 'el canal'}",
        # "/topic": f"Tema actualizado en {argument.split()[0] if argument else 'el canal'}",
        "/names": f"Usuarios en {argument}: {server_response.split(':')[-1] if server_response else ''}",
        "/list": "Lista de canales obtenida",
        "/invite": f"Invitación enviada a {argument.split()[0] if argument else 'el usuario'}",
        "/kick": f"Usuario {argument.split()[1] if argument and len(argument.split()) > 1 else 'el usuario'} expulsado de {argument.split()[0] if argument else 'el canal'}",
        "/whois": f"Información de {argument}: {server_response.split(':')[-1] if server_response else ''}",
        "/whowas": f"Historial de {argument}: {server_response.split(':')[-1] if server_response else ''}",
        "/who": f"Información de usuarios:",
        "/oper": "Ahora eres un operador de IRC",
        "/kill": f"Conexión de {argument.split()[0] if argument else 'el usuario'} terminada",
        "/wallops": f"Mensaje global enviado: {argument}",
        "/version": f"Versión del servidor: {' '.join(server_response.split()[3:]) if server_response else 'No disponible'}",
        "/stats": "Estadísticas del servidor obtenidas",
        "/links": "Lista de servidores conectados",
        "/time": f"{time if time else 'No disponible'}",
        "/admin": "Información del administrador obtenida",
        "/info": "Información del servidor obtenida",
        "/trace": "Ruta de conexión trazada",
        "/connect": f"Conectando a {argument.split()[0] if argument else 'el servidor'}",
        "/squit": f"Servidor {argument.split()[0] if argument else 'el servidor'} desconectado",
        "/ping": "Ping exitoso",
        "/away": f"Mensaje de ausencia establecido: {argument}",
        "/rehash": "Configuración recargada",
        "/die": "Servidor cerrado",
        "/restart": "Servidor reiniciado",
        "/servlist": "Lista de servicios vacía",
        "/userhost": f"Información de usuario:\n" + "\n".join(server_response.split(":")[-1].strip().split()) if server_response else "No hay información de usuario.",
        "/ison": f"Usuarios conectados: {' '.join(server_response.split(':')[-1].strip().split())}" if server_response else "No hay usuarios conectados.",
        
    }
    return formatted if formatted else mapping.get(command, "Comando no reconocido")

def run_interactive_mode(connection, nick):
    """
    Modo interactivo donde el usuario puede ingresar comandos continuamente.
    """
    while True:
        try:
            # Solicitar comando y argumento al usuario
            user_input = input("Ingrese un comando (o 'quit' para salir): ").strip()
            if not user_input:
                continue

            # Manejar el comando 'quit' para salir
            if user_input.lower() == "quit" or user_input.startswith("/quit"):
                parts = user_input.split(" ", 1)  # Dividir en máximo 2 partes
                command = parts[0]  # Siempre será "/quit" o "quit"
                argument = parts[1] if len(parts) > 1 else ""  # Argumento vacío si no hay
                connection.quit(argument)
                print(f"Desconectado del servidor")
                # if not execute_command(connection, command, argument, nick):
                #     break  # Salir si el comando es /quit o hay un error grave
                break
            
            
            # Dividir el comando y el argumento
            parts = user_input.split(" ", 1)
            command = parts[0]
            argument = parts[1] if len(parts) > 1 else ""

            # Ejecutar el comando
            if not execute_command(connection, command, argument, nick):
                break  # Salir si el comando es /quit o hay un error grave

        except KeyboardInterrupt:
            print("\nSaliendo del cliente IRC...")
            connection.quit("Saliendo del cliente IRC")
            break
        except Exception as e:
            print(f"Error inesperado: {e}")

def run_single_command_mode(host, port, nick, command, argument):
    try:
        connection = ClientConnection(host, port)
        connection.connect_client("pass", "user", nick)
        start_receiver_thread(connection)
        if not execute_command(connection, command, argument, nick):
            return
        # Esperar 1 segundo para recibir respuestas
        time.sleep(1)
        connection.quit("Goodbye!")
    except IRCConnectionError as e:
        print(f"Error de conexión: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

def parse_arguments():
    """
    Parsea los argumentos de línea de comandos manualmente.
    """
    args = {
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "nick": None,
        "command": None,
        "argument": None,
    }

    # Simulamos el parsing de argumentos manualmente
    import os
    argv = os.sys.argv[1:]  # Obtenemos los argumentos sin el nombre del script

    i = 0
    while i < len(argv):
        if argv[i] == "-H" and i + 1 < len(argv):
            args["host"] = argv[i + 1]
            i += 1
        elif argv[i] == "-p" and i + 1 < len(argv):
            args["port"] = argv[i + 1]
            i += 1
        elif argv[i] == "-n" and i + 1 < len(argv):
            args["nick"] = argv[i + 1]
            i += 1
        elif argv[i] == "-c" and i + 1 < len(argv):
            args["command"] = argv[i + 1]
            i += 1
        elif argv[i] == "-a" and i + 1 < len(argv):
            args["argument"] = argv[i + 1]
            i += 1
        i += 1

    return args

if __name__ == "__main__":
    # Parsear argumentos manualmente
    args = parse_arguments()
    time.sleep(5)
    if args["command"] and args["argument"]:
        # Modo de un solo comando (para testers)
        run_single_command_mode(args["host"], args["port"], args["nick"], args["command"], args["argument"])
    else:
        # Modo interactivo (para uso manual)
        try:
            connection = ClientConnection(args["host"], args["port"])
            connection.connect_client("pass", "user", args["nick"] if args["nick"] else "Guest")

            # Iniciar el hilo de recepción
            start_receiver_thread(connection)

            # Ejecutar el modo interactivo
            run_interactive_mode(connection, args["nick"])
        except IRCConnectionError as e:
            print(f"Error de conexión: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")