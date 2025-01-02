def parse_message(raw_message):
    """Parsea un mensaje en formato IRC."""
    try:
        prefix = ''
        if raw_message.startswith(':'):
            prefix, raw_message = raw_message[1:].split(' ', 1)
        if ' :' in raw_message:
            args, trailing = raw_message.split(' :', 1)
            return prefix, args.split(), trailing
        else:
            return prefix, raw_message.split(), None
    except Exception:
        raise ProtocolError("Error al parsear el mensaje")

def build_message(command, params=None, trailing=None):
    """Construye un mensaje en formato IRC."""
    message = command
    if params:
        message += ' ' + ' '.join(params)
    if trailing:
        message += ' :' + trailing
    return message
