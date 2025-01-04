
RESPONSES = {
    "JOIN_SUCCESS": ":mock.server 332 {nickname} {channel} :Bienvenido al canal {channel}\r\n",
    "PART_SUCCESS": ":mock.server 333 {nickname} {channel} :{nickname} ha salido del canal\r\n",
    "ERR_NO_SUCH_CHANNEL": ":mock.server 403 {target} :No existe el canal\r\n",
    "ERR_NO_SUCH_NICK": ":mock.server 401 {target} :El usuario no está conectado\r\n",
    "ERR_NOT_IN_CHANNEL": ":mock.server 442 {nickname} {channel} :No estás en el canal\r\n",
}
