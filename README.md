# Repositorio para la entrega de proyectos de la asignatura de Redes de Computadoras. Otoño 2024 - 2025

### Requisitos para la ejecución de las pruebas:

1. Ajustar la variable de entorno `procotol` dentro del archivo `env.sh` al protocolo correspondiente. 

2. Modificar el archivo `run.sh` con respecto a la ejecución de la solución propuesta.

### Ejecución de los tests:

1. En cada fork del proyecto principal, en el apartado de `actions` se puede ejecutar de forma manual la verificación del código propuesto.

2. Abrir un `pull request` en el repo de la asignatura a partir de la propuesta con la solución.

### Descripción general del funcionamineto de las pruebas:

Todas las pruebas siguen un modelo de ejecución simple. Cada comprobación ejecuta un llamado al scrip `run.sh` contenido en la raíz del proyecto, inyectando los parametros correspondientes.

La forma de comprobación es similar a todos los protocolos y se requiere que el ejecutable provisto al script `run.sh` sea capaz de, en cada llamado, invocar el método o argumento provisto y terminar la comunicación tras la ejecución satisfactoria del metodo o funcionalidad provista.

### Argumentos provistos por protocolo:

#### HTTP:
1. -m method. Ej. `GET`
2. -u url. Ej `http://localhost:4333/example`
3. -h header. Ej `{}` o `{"User-Agent": "device"}`
4. -d data. Ej `Body content`

#### SMTP:
1. -p port. Ej. `25`
2. -u host. Ej `127.0.0.1`
3. -f from_mail. Ej. `user1@uh.cu`
4. -f to_mail. Ej. `["user2@uh.cu", "user3@uh.cu"]`
5. -s subject. Ej `"Email for testing purposes"`
6. -b body. Ej `"Body content"`
7. -h header. Ej `{}` o ```{"CC": "cc@examplecom"}```

#### FTP:
1. -p port. Ej. `21`
2. -h host. Ej `127.0.0.1`
3. -u user. Ej. `user`
4. -w pass. Ej. `pass`
5. -c command. Ej `STOR`
6. -a first argument. Ej `"tests/ftp/new.txt"`
7. -b second argument. Ej `"new.txt"`

#### IRC
1. -p port. Ej. `8080`
2. -H host. Ej `127.0.0.1`
3. -n nick. Ej. `TestUser1`
4. -c command. Ej `/nick`
5. -a argument. Ej `"NewNick"`

### Comportamiento de la salida esperada por cada protocolo:

1. ``HTTP``: Json con formato ```{"status": 200, "body": "server output"}```

2. ``SMTP``: Json con formato ```{"status_code": 333, "message": "server output"}```

3. ``FTP``: Salida Unificada de cada interacción con el servidor.

4. ``IRC``:  Salida Unificada de cada interacción con el servidor.
