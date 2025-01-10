from client_network import ClientConnection
#from client_gui import start_gui
from Common.shared_constants import DEFAULT_HOST, DEFAULT_PORT
import threading
from Common.custom_errors import IRCConnectionError

def listen_for_messages(connection):
    while True:
        try:
            response = connection.receive()
            if response:
                print(f"Mensaje del servidor: {response}")
        except IRCConnectionError as e:
            print(f"Error al recibir mensaje: {e}")
            break

        print("Conexión establecida con el servidor IRC.")
def run_client():
    try:
        connection = ClientConnection(DEFAULT_HOST, DEFAULT_PORT)
        connection.connect_client("pass","lia","Lia")  # Inicia la conexión
        #start_gui(connection)  # Lanza la interfaz gráfica
        
        print("Conexión establecida con el servidor IRC.")
        # Inicia un hilo para escuchar mensajes del servidor
        listener_thread = threading.Thread(target=listen_for_messages, args=(connection,))
        listener_thread.daemon = True
        listener_thread.start()
        # Menú interactivo para probar comandos
        while True:
            # Menú interactivo
            print("\n--- Menú de Comandos ---")
            print("1. PASS")
            print("2. USER")
            print("3. NICK")
            print("4. OPER")
            print("5. QUIT")
            print("6. SQUIT")
            print("7. SERVICE")
            print("8. JOIN")
            print("9. PART")
            print("10. MODE")
            print("11. TOPIC")
            print("12. NAMES")
            print("13. LIST")
            print("14. INVITE")
            print("15. KICK")
            print("16. MOTD")
            print("17. LUSERS")
            print("18. VERSION")
            print("19. STATS")
            print("20. LINKS")
            print("21. TIME")
            print("22. CONNECT")
            print("23. SERVLIST")
            print("24. SQUERY")
            print("25. TRACE")
            print("26. ADMIN")
            print("27. INFO")
            print("28. PRIVMSG")
            print("29. NOTICE")
            print("30. WHO")
            print("31. WHOIS")
            print("32. WHOWAS")
            print("33. PING")
            print("34. AWAY")
            print("35. REHASH")
            print("36. DIE")
            print("37. RESTART")
            print("38. KILL")
            print("39. ERROR")
            print("40. SUMMON")
            print("41. USERS")
            print("42. WALLOPS")
            print("43. USERHOST")
            print("44. ISON")
            print("45. Salir")
            
            option = input("Elige una opción: ")
            
            try:
                if option == "1":
                    password = input("Introduce la contraseña: ")
                    connection.pass_command(password)
                elif option == "2":
                    username = input("Introduce el nombre de usuario: ")
                    realname = input("Introduce el nombre real: ")
                    connection.set_user(username, realname)
                elif option == "3":
                    nickname = input("Introduce el apodo: ")
                    connection.nick(nickname)
                elif option == "4":
                    oper_name = input("Introduce el nombre de operador: ")
                    password = input("Introduce la contraseña de operador: ")
                    connection.oper(oper_name, password)
                elif option == "5":
                    quit_message = input("Introduce un mensaje de desconexión (opcional): ")
                    connection.quit(quit_message)
                elif option == "6":
                    target_server = input("Introduce el nombre del servidor a desconectar: ")
                    comment = input("Introduce un comentario: ")
                    connection.squit(target_server, comment)
                elif option == "7":
                    nickname = input("Introduce el nombre del servicio: ")
                    reserved = input("Introduce el campo reservado: ")
                    distribution = input("Introduce la distribución del servicio: ")
                    service_type = input("Introduce el tipo de servicio: ")
                    reserved_2 = input("Introduce el segundo campo reservado: ")
                    info = input("Introduce información adicional del servicio: ")
                    connection.service(nickname, reserved, distribution, service_type, reserved_2, info)
                elif option == "8":
                    channel = input("Introduce el canal (e.g., #general): ")
                    connection.join_channel(channel)
                elif option == "9":
                    channel = input("Introduce el canal del que quieres salir: ")
                    connection.part_channel(channel)
                elif option == "10":
                    target = input("Introduce el usuario o canal objetivo: ")
                    mode = input("Introduce el modo a aplicar: ")
                    params = input("Introduce parámetros adicionales (opcional): ")
                    connection.change_mode(target, mode, params or None)
                elif option == "11":
                    channel = input("Introduce el canal: ")
                    new_topic = input("Introduce el nuevo tema (opcional): ")
                    connection.change_topic(channel, new_topic)
                elif option == "12":
                    channel = input("Introduce el canal para listar usuarios: ")
                    connection.names(channel)
                elif option == "13":
                    connection.list()
                elif option == "14":
                    user = input("Introduce el usuario a invitar: ")
                    channel = input("Introduce el canal: ")
                    connection.invite(user, channel)
                elif option == "15":
                    channel = input("Introduce el canal: ")
                    user = input("Introduce el usuario a expulsar: ")
                    reason = input("Introduce el motivo (opcional): ")
                    connection.kick(channel, user, reason or "Expulsado")
                elif option == "16":
                    connection.motd()
                elif option == "17":
                    connection.lusers()
                elif option == "18":
                    connection.version()
                elif option == "19":
                    connection.stats()
                elif option == "20":
                    connection.links()
                elif option == "21":
                    connection.time()
                elif option == "22":
                    target_server = input("Introduce el servidor objetivo: ")
                    port = input("Introduce el puerto: ")
                    connection.connect_servers(target_server, port)
                elif option == "23":
                    mask = input("Introduce una máscara (opcional): ")
                    service_type = input("Introduce el tipo de servicio (opcional): ")
                    connection.servlist(mask or None, service_type or None)
                elif option == "24":
                    service_name = input("Introduce el nombre del servicio: ")
                    text = input("Introduce el mensaje: ")
                    connection.squery(service_name, text)
                elif option == "25":
                    connection.trace()
                elif option == "26":
                    connection.admin()
                elif option == "27":
                    connection.info()
                elif option == "28":
                    target = input("Introduce el destinatario (usuario o canal): ")
                    message = input("Introduce el mensaje: ")
                    connection.message(target, message)
                elif option == "29":
                    target = input("Introduce el destinatario (usuario o canal): ")
                    message = input("Introduce el mensaje: ")
                    connection.notice(target, message)
                elif option == "30":
                    mask = input("Introduce una máscara (opcional): ")
                    connection.who(mask)
                elif option == "31":
                    user = input("Introduce el nombre del usuario: ")
                    connection.whois(user)
                elif option == "32":
                    user = input("Introduce el nombre del usuario: ")
                    connection.whowas(user)
                elif option == "33":
                    server_name = input("Introduce el nombre del servidor: ")
                    connection.ping(server_name)
                elif option == "34":
                    message = input("Introduce un mensaje de ausencia: ")
                    connection.away(message)
                elif option == "35":
                    connection.rehash()
                elif option == "36":
                    connection.die()
                elif option == "37":
                    connection.restart()
                elif option == "38":
                    target = input("Introduce el nombre del usuario a expulsar: ")
                    comment = input("Introduce un comentario: ")
                    connection.kill(target, comment)
                elif option == "39":
                    message = input("Introduce el mensaje de error: ")
                    connection.error(message)
                elif option == "40":
                    user = input("Introduce el nombre del usuario a notificar: ")
                    server = input("Introduce el servidor objetivo (opcional): ")
                    connection.summon(user, server or None)
                elif option == "41":
                    server = input("Introduce el servidor objetivo (opcional): ")
                    connection.users(server or None)
                elif option == "42":
                    message = input("Introduce el mensaje para los operadores: ")
                    connection.wallops(message)
                elif option == "43":
                    nicks = input("Introduce los apodos a consultar (separados por espacio): ").split()
                    connection.userhost(*nicks)
                elif option == "44":
                    nicks = input("Introduce los apodos a verificar (separados por espacio): ").split()
                    connection.ison(*nicks)
                elif option == "45":
                    print("Saliendo...")
                    break
                else:
                    print("Opción no válida. Intenta de nuevo.")
                
            except Exception as e:
                print(f"Error al ejecutar el comando: {e}")
            # Recibir y mostrar respuesta después de cada comando
            # response = connection.receive()
            # print("Respuesta del servidor:", response)
    except Exception as e:
        print(f"Error al iniciar el cliente: {e}")

run_client()