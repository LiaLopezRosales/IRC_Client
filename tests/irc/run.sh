#!/bin/bash

failed=0

# Test 1: Conectar, establecer y cambiar nickname
echo "Running Test 1: Conectar, establecer y cambiar nickname"
./tests/irc/exec.sh -H "localhost" -p "8080" -n "TestUser1" -c "/nick" -a "NuevoNick"
if [[ $? -ne 0 ]]; then
  echo "Test 1 failed"
  failed=1
fi

# Test 2: Entrar a un canal
echo "Running Test 2: Entrar a un canal"
./tests/irc/exec.sh  -H "localhost" -p "8080" -n "TestUser1" -c "/join" -a "#Nuevo"
if [[ $? -ne 0 ]]; then
  echo "Test 2 failed"
  failed=1
fi

# Test 3: Enviar un mensaje a un canal
echo "Running Test 3: Enviar un mensaje a un canal"
./tests/irc/exec.sh  -H "localhost" -p "8080" -n "TestUser1" -c "/notice" -a "#General Hello, world!"
if [[ $? -ne 0 ]]; then
  echo "Test 3 failed"
  failed=1
fi

# Test 4: Salir de un canal
echo "Running Test 4: Salir de un canal"
./tests/irc/exec.sh  -H "localhost" -p "8080" -n "NewNick" -c "/part" -a "#General"
if [[ $? -ne 0 ]]; then
  echo "Test 5 failed"
  failed=1
fi

# Test 5: Desconectar del servidor
echo "Running Test 5: Desconectar del servidor"
./tests/irc/exec.sh  -H "localhost" -p "8080" -n "NewNick" -c "/quit" -a "Goodbye!"
if [[ $? -ne 0 ]]; then
  echo "Test 6 failed"
  failed=1
fi

if [[ $failed -ne 0 ]]; then
  echo "Tests failed"
  exit 1
fi

echo "All custom tests completed successfully"