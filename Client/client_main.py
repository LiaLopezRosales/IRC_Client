import threading
from client_network import ClientConnection
from Common.shared_constants import DEFAULT_HOST, DEFAULT_PORT
from Common.custom_errors import IRCConnectionError

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

def execute_command(connection, command, argument):
    """
    Ejecuta un comando específico en la conexión IRC.
    """
    try:
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
            return False  # Indica que el cliente debe cerrarse
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

        return True  # Continúa en modo interactivo

    except IRCConnectionError as e:
        print(f"Error de conexión: {e}")
        return False  # Cierra el cliente
    except Exception as e:
        print(f"Error inesperado: {e}")
        return True  # Continúa en modo interactivo

def run_interactive_mode(connection):
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
            if user_input.lower() == "quit":
                connection.quit("Saliendo del cliente IRC")
                break

            # Dividir el comando y el argumento
            parts = user_input.split(" ", 1)
            command = parts[0]
            argument = parts[1] if len(parts) > 1 else ""

            # Ejecutar el comando
            if not execute_command(connection, command, argument):
                break  # Salir si el comando es /quit o hay un error grave

        except KeyboardInterrupt:
            print("\nSaliendo del cliente IRC...")
            connection.quit("Saliendo del cliente IRC")
            break
        except Exception as e:
            print(f"Error inesperado: {e}")

def run_single_command_mode(host, port, nick, command, argument):
    """
    Modo de un solo comando para uso con testers.
    """
    try:
        connection = ClientConnection(host, port)
        connection.connect_client("pass", "user", nick)  # Inicia la conexión

        # Iniciar el hilo de recepción
        start_receiver_thread(connection)

        # Ejecutar el comando especificado
        if not execute_command(connection, command, argument):
            return  # Salir si el comando es /quit o hay un error grave

        # Cerrar la conexión
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
            run_interactive_mode(connection)
        except IRCConnectionError as e:
            print(f"Error de conexión: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")