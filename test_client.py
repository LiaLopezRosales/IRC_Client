# text_client.py

import time
from Client.client_network import ClientConnection
from mock_server import MockIRCServer
from Common.shared_constants import DEFAULT_HOST, DEFAULT_PORT

def test_client_advanced():
    """
    Prueba avanzada para validar todas las funciones del RFC 2812.
    """
    print("\n=== INICIANDO PRUEBA COMPLETA DEL CLIENTE ===\n")
    
    # Iniciar servidor simulado (Mock)
    server = MockIRCServer(DEFAULT_HOST, DEFAULT_PORT)
    server.start()
    time.sleep(1)

    # Crear cliente y conectarlo
    client = ClientConnection(DEFAULT_HOST, DEFAULT_PORT)
    try:
        # Conectar y realizar los pasos básicos de registro
        print("[TEST] Conectando y registrando cliente...")
        client.connect()
        client.send("NICK", trailing="TestUser")
        client.send("USER", trailing="TestUser * * :Ariadna")

        # Unirse a un canal y enviar mensajes
        client.send("JOIN", trailing="#general")
        client.send_message("#general", "¡Hola a todos!")
        
        # Enviar un mensaje NOTICE
        client.send_notice("#general", "Este es un mensaje NOTICE.")
        
        # Comprobar que el servidor responde correctamente a PRIVMSG
        print("\n[TEST] Enviando un mensaje PRIVMSG...")
        client.send("PRIVMSG", trailing="#general :Este es un mensaje de prueba")

        # Enviar PING y esperar la respuesta PONG
        print("\n[TEST] Enviando PING y esperando respuesta PONG...")
        client.ping("mock.server")

        # Simular un cliente saliendo de un canal (PART)
        client.send("PART", trailing="#general")
        
        # Desconectar (QUIT)
        print("\n[TEST] Enviando QUIT...")
        client.send("QUIT", trailing="Desconectar del servidor")

        # Esperar que el cliente haya manejado todo correctamente
        time.sleep(2)

    except Exception as e:
        print(f"[ERROR] Error durante la prueba avanzada: {e}")
    
    finally:
        client.close()
        server.stop()
        print("\n=== PRUEBA COMPLETA FINALIZADA ===\n")

# Ejecutar la prueba
if __name__ == "__main__":
    test_client_advanced()
