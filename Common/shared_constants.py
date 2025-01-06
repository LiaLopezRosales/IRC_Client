# shared_constants.py

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6667

# Comandos estándar del protocolo IRC (RFC 2812)
IRC_COMMANDS = {
    "USER": "Registra al usuario con detalles adicionales",
    "OPER": "Otorga privilegios de operador",
    "QUIT": "Desconectarse del servidor",
    "JOIN": "Unirse a un canal",
    "PART": "Salir de un canal",
    "MODE": "Cambia el modo de un usuario o canal",
    "TOPIC": "Establece o consulta el tema del canal",
    "NAMES": "Lista los usuarios de un canal",
    "LIST": "Lista canales disponibles",
    "INVITE": "Invitar a un usuario a un canal",
    "KICK": "Expulsar a un usuario de un canal",
    "VERSION": "Solicitar la versión del servidor",
    "STATS": "Solicitar estadísticas del servidor",
    "LINKS": "Lista servidores conectados",
    "TIME": "Consulta la hora del servidor",
    "CONNECT": "Conectar a otro servidor",
    "TRACE": "Traza la ruta de conexión",
    "ADMIN": "Información del administrador del servidor",
    "INFO": "Información del servidor",
    "PRIVMSG": "Enviar un mensaje privado",
    "NOTICE": "Enviar una notificación sin respuesta",
    "WHO": "Consulta información sobre usuarios",
    "WHOIS": "Consulta información detallada de un usuario",
    "WHOWAS": "Consulta información sobre un usuario desconectado",
    "PING": "Verificar la latencia con el servidor",
    "PONG": "Responder a un PING",
    "AWAY": "Establecer mensaje de ausencia",
    "REHASH": "Recargar configuración del servidor",
    "DIE": "Cerrar el servidor (operadores)",
    "RESTART": "Reiniciar el servidor"
}
