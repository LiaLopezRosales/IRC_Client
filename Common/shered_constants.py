# shared_constants.py

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6667

# Comandos estándar del protocolo IRC (RFC 2812)
IRC_COMMANDS = {
    "NICK": "Establece o cambia el apodo del cliente",
    "USER": "Registra al usuario con detalles adicionales",
    "JOIN": "Unirse a un canal",
    "PART": "Salir de un canal",
    "PRIVMSG": "Enviar un mensaje privado a otro usuario o canal",
    "NOTICE": "Enviar un mensaje de notificación",
    "PING": "Verificar si el servidor está activo",
    "PONG": "Respuesta al comando PING",
    "QUIT": "Desconectarse del servidor",
}
