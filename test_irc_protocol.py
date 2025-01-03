# test_irc_protocol.py

from Common.irc_protocol import parse_message, build_message

def test_irc_protocol():
    # Mensaje crudo simulado
    raw_message = ":server.example.com PING :12345"
    
    # Parsear el mensaje
    prefix, command, params, trailing = parse_message(raw_message)
    assert prefix == "server.example.com"
    assert command == "PING"
    assert params == []
    assert trailing == "12345"
    print("Prueba de parseo: OK")
    
    # Construir un mensaje
    command = "PRIVMSG"
    params = ["#channel"]
    trailing = "Hola a todos"
    built_message = build_message(command, params, trailing)
    expected_message = "PRIVMSG #channel :Hola a todos"
    assert built_message == expected_message
    print("Prueba de construcción: OK")
    
if __name__ == "__main__":
    test_irc_protocol()
