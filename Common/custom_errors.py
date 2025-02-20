# Common.custom_errors.py

class IRCConnectionError(Exception):
    """Error en la conexión al servidor."""
    pass

class ProtocolError(Exception):
    """Error en el manejo del protocolo IRC."""
    pass
