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
    "/nick": f":.* NICK :{argument}",
    "/join": f":.* JOIN :{argument}",
    "/part": f":.* PART :{argument}",
    "/privmsg": f":{nick}!.* PRIVMSG {argument.split()[0]}",
    "/notice": f":{nick}!.* NOTICE {argument.split()[0]}",
    "/quit": "ERROR :Closing link",
    "/mode": r" MODE ",
    "/topic": r" TOPIC ",
    "/names": (r' 353 ', r' 366 '),
    "/list": (r' 322 ', r' 323 '),
    "/invite": r" INVITE ",
    "/kick": r" KICK ",
    "/who": (r' 352 ', r' 315 '),
    "/whois": (r' 311 ', r' 318 '),
    "/whowas": r" 314 ",
    "/oper": r" 381 ",
    "/kill": r" KILL ",
    "/wallops": r" WALLOPS ",
    "/version": r" 351 ",
    "/stats": r" 248 ",
    "/links": r" 364 ",
    "/time": r" 391 ",
    "/admin": r" 256 ",
    "/info": r" 371 ",
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
    "ERROR": {
        "403": "No existe el canal",
        "482": "No tienes permiso para realizar esta acción",
        "481": "Necesitas privilegios de operador",
        "431": "Falta nickname",
        "433": "Nickname ya está en uso",
        "476": "Nombre de canal inválido"
    }
}


    try:
        if command in ["/list", "/names", "/who", "/whois"]:
            pattern, terminator = response_patterns[command]
            connection.set_expected_response(pattern, terminator)
        elif command in response_patterns:
            connection.set_expected_response(response_patterns[command])
        else:
            connection.set_expected_response(None)
            
        if command == "/nick":
            connection.nick(argument)
        elif command == "/join":
            connection.join_channel(argument)
        elif command == "/part":
            connection.part_channel(argument)
        elif command == "/notice":
            target, message = argument.split(" ", 1)
            connection.notice(target, message)
        elif command == "/quit":
            connection.quit(argument)
            #return False  # Indica que el cliente debe cerrarse
        elif command == "/privmsg":
            target, message = argument.split(" ", 1)
            connection.message(target, message)
        elif command == "/mode":
            target, mode = argument.split(" ", 1)
            connection.change_mode(target, mode)
        elif command == "/topic":
            channel, topic = argument.split(" ", 1)
            connection.change_topic(channel, topic)
        elif command == "/names":
            connection.names(argument)
        elif command == "/list":
            connection.list()
        elif command == "/invite":
            user, channel = argument.split(" ", 1)
            connection.invite(user, channel)
        elif command == "/kick":
            channel, user = argument.split(" ", 1)
            connection.kick(channel, user)
        elif command == "/who":
            connection.who(argument)
        elif command == "/whois":
            connection.whois(argument)
        elif command == "/whowas":
            connection.whowas(argument)
        elif command == "/oper":
            name, password = argument.split(" ", 1)
            connection.oper(name, password)
        elif command == "/kill":
            target, comment = argument.split(" ", 1)
            connection.kill(target, comment)
        elif command == "/wallops":
            connection.wallops(argument)
        elif command == "/version":
            connection.version()
        elif command == "/stats":
            connection.stats()
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
            target_server, port = argument.split(" ", 1)
            connection.connect_servers(target_server, port)
        elif command == "/squit":
            server, comment = argument.split(" ", 1)
            connection.squit(server, comment)
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
    "/nick": f":.* NICK {argument}",
    "/join": f":.* JOIN {argument}",
    "/part": f":.* PART {argument}",
    "/privmsg": f":{nick}!.* PRIVMSG {argument.split()[0]}",
    "/notice": f":{nick}!.* NOTICE {argument.split()[0]}",
    "/quit": "ERROR :Closing link",
    "/mode": r" MODE ",
    "/topic": r" TOPIC ",
    "/names": (r' 353 ', r' 366 '),
    "/list": (r' 322 ', r' 323 '),
    "/invite": r" INVITE ",
    "/kick": r" KICK ",
    "/who": (r' 352 ', r' 315 '),
    "/whois": (r' 311 ', r' 318 '),
    "/whowas": r" 314 ",
    "/oper": r" 381 ",
    "/kill": r" KILL ",
    "/wallops": r" WALLOPS ",
    "/version": r" 351 ",
    "/stats": r" 248 ",
    "/links": r" 364 ",
    "/time": r" 391 ",
    "/admin": r" 256 ",
    "/info": r" 371 ",
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
    "ERROR": {
        "403": "No existe el canal",
        "482": "No tienes permiso para realizar esta acción",
        "481": "Necesitas privilegios de operador",
        "431": "Falta nickname",
        "433": "El apodo ya está en uso",
        "476": "Nombre de canal inválido"
    }
}
    if isinstance(server_response, list):
        server_response = " ".join(server_response)

    error_messages = response_patterns.get("ERROR", {})
    formatted = []
    #print(f"server {server_response}")
    parts = server_response.split()
    if len(parts) > 1 and parts[1].isdigit() and parts[1] in response_patterns["ERROR"]:
        return response_patterns["ERROR"][parts[1]]
    
    for response in server_response or []:
        parts = response.split()
        # print(response)
        
        # Detectar errores (solo si la respuesta tiene un código numérico)
        if len(parts) > 1 and parts[1].isdigit() and parts[1] in error_messages:
            # print(f"3")
            return error_messages[parts[1]]
        
        # Formatear respuestas multiparte
        if command == "/list":
            if isinstance(server_response, str):  
                server_response = server_response.split("\n")  # Convertirlo en lista si es necesario
            if ' 322 ' in response:
                parts = response.split()
                formatted.append(f"Canal: {parts[3]} - Usuarios: {parts[4]} - Tema: {' '.join(parts[5:])}")
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
                server_response = server_response.split("\n")
            for response in server_response:
                if ' 352 ' in response:  # Línea con datos de usuario
                    parts = response.split()
                    username = parts[7]
                    channel = parts[3]
                    ip = parts[4]
                    real_name = " ".join(parts[9:])  # Captura el nombre real al final
                    formatted.append(f"Usuario: {username} - Canal: {channel} - IP: {ip} - Nombre: {real_name}")
                elif ' 315 ' in response:  # Fin de /WHO
                    break
            return formatted if formatted else "Información de usuarios obtenida"

        elif command == "/whois":
            if ' 311 ' in response:
                parts = response.split()
                formatted.append(f"Información de {parts[3]}: Usuario real: {parts[4]} - Host: {parts[5]}")
            elif ' 312 ' in response:
                parts = response.split()
                formatted.append(f"Servidor: {parts[3]} - {parts[4]}")
                
    mapping = {
        "/nick": f"Tu nuevo apodo es {argument}",
        "/join": f"Te has unido al canal {argument}",
        "/part": f"Has salido del canal {argument}",
        "/privmsg": f"Mensaje enviado: {argument}",
        "/notice": f"Notificacion de {nick}: {argument}",
        "/quit": "Desconectado del servidor",
        "/mode": f"Modo cambiado en {argument.split()[0] if argument else 'el canal'}",
        "/topic": f"Tema actualizado en {argument.split()[0] if argument else 'el canal'}",
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
        "/version": f"Versión del servidor: {server_response.split()[-1] if server_response else ''}",
        "/stats": "Estadísticas del servidor obtenidas",
        "/links": "Lista de servidores conectados",
        "/time": f"Hora del servidor: {server_response.split(':')[-1] if server_response else ''}",
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
        "/userhost": f"Información de usuario: {server_response.split()[-1] if server_response else ''}",
        "/ison": f"Usuarios conectados: {server_response.split()[-1] if server_response else ''}",
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