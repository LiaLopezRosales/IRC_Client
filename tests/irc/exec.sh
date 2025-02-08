#!/bin/bash

# Función para mostrar ayuda
function show_help() {
    echo "Uso: ./exec.sh -H <direccion_ip> -p <puerto> -n <nick> -c <comando> -a <argumento>"
}

# Variables por defecto
host="localhost"
port="8080"
nick="NICK"  # Valor por defecto para el nick
command=""
argument=""

# Procesar argumentos
while getopts "H:p:n:c:a:" opt; do
    case $opt in
        H) host="$OPTARG" ;;
        p) port="$OPTARG" ;;
        n) nick="$OPTARG" ;;  # Capturar el valor de -n
        c) command="$OPTARG" ;;
        a) argument="$OPTARG" ;;
        *) show_help
           exit 1 ;;
    esac
done

# Verificar que los argumentos requeridos estén presentes
if [ -z "$command" ] || [ -z "$argument" ]; then
    show_help
    exit 1
fi

# Ejecutar el cliente IRC con los parámetros
output=$(./run.sh -H "$host" -p "$port" -n "$nick" -c "$command" -a "$argument")

# Verificar la salida del cliente según el comando enviado
case "$command" in
    "/nick")
        expected_response="Tu nuevo apodo es $argument"
        ;;
    "/join")
        expected_response="Te has unido al canal $argument"
        ;;
    "/part")
        expected_response="Has salido del canal $argument"
        ;;
    "/privmsg")
        expected_response="Mensaje de $nick: $argument"
        ;;
    "/notice")
        expected_response="Notificacion de $nick: $argument"
        ;;
    "/list")
        expected_response="Lista de canales:"
        ;;
    "/names")
        expected_response="Usuarios en el canal $argument:"
        ;;
    "/whois")
        expected_response="Usuario $argument en el canal"
        ;;
    "/topic")
        expected_response="El topic del canal $argument es:"
        ;;
    "/quit")
        expected_response="Desconectado del servidor"
        ;;
    *)
        echo "Comando no reconocido: $command"
        exit 1
        ;;
esac

# Verificar si la salida del cliente coincide con lo esperado
if [[ "$output" == *"$expected_response"* ]]; then
    echo -e "\e[32mPrueba exitosa: La salida del cliente coincide con lo esperado.\e[0m"
    exit 0
else
    echo -e "\e[31mPrueba fallida: La salida del cliente no coincide con lo esperado.\e[0m"
    echo -e "\e[31mEsperado: $expected_response\e[0m"
    echo -e "\e[31mObtenido: $output\e[0m"
    exit 1
fi