# irc_protocol.py

from Common.custom_errors import ProtocolError


def parse_message(raw_message):
    """
    Parsear un mensaje IRC recibido desde el servidor o cliente.
    
    El formato esperado es: 
    [":" <prefix> <SPACE>] <command> <params> [<SPACE> ":" <trailing>]
    
    - `prefix` es opcional, indica la fuente del mensaje (e.g., servidor o cliente).
    - `command` es el comando IRC (e.g., NICK, JOIN, PRIVMSG).
    - `params` son los parámetros asociados al comando.
    - `trailing` es el mensaje final (e.g., texto de un chat).
    
    Args:
        raw_message (str): Mensaje IRC crudo recibido.
    
    Returns:
        tuple: (prefix, command, params, trailing).
    """
    try:
        prefix = ''
        trailing = None
        if raw_message.startswith(':'):
            prefix, raw_message = raw_message[1:].split(' ', 1)

        if ' :' in raw_message:
            raw_message, trailing = raw_message.split(' :', 1)

        parts = raw_message.split()
        if not parts:
            raise ProtocolError("Mensaje IRC inválido: Falta el comando")

        command = parts[0]
        params = parts[1:]

        return prefix, command, params, trailing
    
    except Exception as e:
        raise ProtocolError(f"Error al parsear el mensaje: {e}")


def build_message(command, params=None, trailing=None):
    """
    Construir un mensaje IRC para enviar al servidor o cliente.
    
    El formato generado será:
    [":" <prefix> <SPACE>] <command> <params> [<SPACE> ":" <trailing>]
    
    Args:
        command (str): Comando IRC (e.g., NICK, JOIN, PRIVMSG).
        params (list, optional): Lista de parámetros asociados al comando.
        trailing (str, optional): Mensaje adicional (texto del chat o similar).
    
    Returns:
        str: Mensaje formateado listo para enviar.
    """
    try:
        if not command:
            raise ProtocolError("El comando no puede estar vacío")

        message = command
        
        # Verificar si hay parámetros y evitar concatenar None
        if params:
            # Si los parámetros son una lista, asegurar que cada parámetro con espacios esté correctamente delimitado.
            message += ' ' + ' '.join([str(param) if param else '' for param in params])

        if trailing:
            message += ' :' + trailing
   
        return message
    except Exception as e:
        raise ProtocolError(f"Error al construir el mensaje: {e}")
