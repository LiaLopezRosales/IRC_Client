import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import textwrap
from client_network import ClientConnection
from Common.shared_constants import DEFAULT_HOST, DEFAULT_PORT
import threading
from Common.custom_errors import ProtocolError
import queue
from Common.irc_protocol import parse_message


class MainView(tk.Tk):
    """
    Vista principal para el cliente IRC. Contiene:
    - Menú lateral desplegable.
    - Lista de canales/usuarios.
    - Área de chat.
    - Cinta de estado.
    - Cinta de información del chat abierto.
    """
    
    def __init__(self):
        super().__init__()
        self.title("Cliente IRC - UI Moderna")
        self.geometry("1000x700")
        self.configure(bg="#1E1E1E")  # Fondo oscuro
        
        # Conexión al servidor IRC
        self.connection = None
        self.server_messages = queue.Queue()  # Para mensajes generales
        self.channel_list_queue = queue.Queue()  # Para respuestas de LIST
        self.user_list_queue = queue.Queue()  # Para respuestas de WHO
        
        # Variables de estado
        self.active_target = tk.StringVar(value="Servidor")
        # self.active_target.set("Servidor")
        self.active_target_type = -1
        self.connected = tk.StringVar(value="Desconectado")
        self.is_authenticated = False  # Usuario autenticado
        self.is_connected = False  # Estado de conexión al servidor
        self.username = None
        self.password = None
        self.nick = None

        # Flujo de mensajes
        self.message_history = {}  # Diccionario para almacenar mensajes
        self.new_message_indicators = {}  # Para marcar nuevos mensajes

        # Diccionario para canales: {channel_name: {"topic": str}}
        self.channels = {"Servidor": {"topic": "Mensajes del servidor"}}  # Canal predeterminado

        # Conjunto para usuarios únicos en el servidor
        self.all_users = set()

        # Colores personalizables
        self.colors = {
            "bg": "#1E1E1E",  # Fondo general
            "fg": "#FFFFFF",  # Texto
            "accent": "#007ACC",  # Acento (botones)
            "menu": "#252526",  # Fondo del menú
            "menu_fg": "#D4D4D4",  # Texto del menú
            "disconnect": "#D9534F",  # Rojo para desconectado
            "connect": "#5CB85C",  # Verde para conectado
        }

        # Crear las secciones principales
        self.create_status_bar()
        self.create_sidebar()
        self.create_channel_user_list()
        self.create_chat_area()
     
    def start_receiving(self):
        """Inicia un hilo para escuchar respuestas del servidor."""
        def listen():
            """
            Hilo que escucha mensajes del servidor y los procesa.
            """
            while self.is_connected:
                try:
                    self.connection.receive(self.server_messages)  # Pasa la cola de mensajes
                except Exception as e:
                    print(f"Error al recibir mensaje: {e}")
                    self.is_connected = False
                    self.update_connection_status(False)
                    break

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def create_status_bar(self):
        """Cinta superior con estado de conexión."""
        
        self.status_bar = tk.Label(
            self,
            textvariable=self.connected,
            bg=self.colors["disconnect"],  # Rojo por defecto
            fg="#FFFFFF",
            font=("Arial", 16, "bold"),
            anchor="w",
            padx=475,
        )
        self.status_bar.pack(fill="x")

    def update_connection_status(self, connected=True):
        """Actualiza el estado de conexión."""
        if connected:
            self.connected.set("Conectado")
            self.status_bar.config(bg=self.colors["connect"])
        else:
            self.connected.set("Desconectado")
            self.status_bar.config(bg=self.colors["disconnect"])

    def create_channel_user_list(self):
        """Sección izquierda para lista de canales o usuarios deslizante."""
        self.channel_user_frame = tk.Frame(self, bg=self.colors["bg"], width=320)
        self.channel_user_frame.pack(side="left", fill="both", expand=True)
        self.channel_user_frame.pack_propagate(False)  # Desactiva el ajuste automático

        # Crear el notebook con pestañas deslizables
        self.tabs = ttk.Notebook(self.channel_user_frame)
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Arial", 16))

        # Canales con desplazamiento
        self.channel_list_frame = ttk.Frame(self.tabs)
        self.channel_scrollbar = tk.Scrollbar(self.channel_list_frame)
        self.channel_list = tk.Listbox(
            self.channel_list_frame,
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            yscrollcommand=self.channel_scrollbar.set,
            font=("Arial", 16)  
        )
        self.channel_scrollbar.config(command=self.channel_list.yview)
        self.channel_list.pack(side="left", fill="both", expand=True)
        self.channel_scrollbar.pack(side="right", fill="y")
        # para seleccionar canal
        self.channel_list.bind("<<ListboxSelect>>", self.update_active_target)
        self.tabs.add(self.channel_list_frame, text="Canales")

        
        # Usuarios con desplazamiento
        self.user_list_frame = ttk.Frame(self.tabs)
        self.user_scrollbar = tk.Scrollbar(self.user_list_frame)
        self.user_list = tk.Listbox(
            self.user_list_frame,
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            yscrollcommand=self.user_scrollbar.set,
            font=("Arial", 16)
        )
        self.user_scrollbar.config(command=self.user_list.yview)
        self.user_list.pack(side="left", fill="both", expand=True)
        self.user_scrollbar.pack(side="right", fill="y")
        # para seleccionar usuario
        self.user_list.bind("<<ListboxSelect>>", self.update_active_target)
        self.tabs.add(self.user_list_frame, text="Usuarios")


        # Agregar las pestañas
        self.tabs.add(self.channel_list_frame, text="Canales")
        self.tabs.add(self.user_list_frame, text="Usuarios")
        self.tabs.pack(fill="both", expand=True)

        self.channel_list.config(selectbackground="#4caf50", activestyle="dotbox", height=15)
        self.user_list.config(selectbackground="#4caf50", activestyle="dotbox", height=15)

    def create_chat_area(self):
        """Área de chat principal con ajustes de tamaño y diseño."""
        self.chat_frame = tk.Frame(self, bg=self.colors["bg"], width=460)
        self.chat_frame.pack(side="right", fill="both", expand=True)
        self.chat_frame.pack_propagate(False)  # Desactiva el ajuste automático

        self.create_info_chat_bar()

        # Historial de mensajes
        self.chat_history = scrolledtext.ScrolledText(
            self.chat_frame,
            state="disabled",
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            wrap="word",
            font=("Arial", 14)
        )
        self.chat_history.pack(expand=True, fill="both", pady=5)

        # Área de entrada y botón al lado
        self.message_frame = tk.Frame(self.chat_frame, bg=self.colors["bg"])
        self.message_frame.pack(fill="x")

        self.message_entry = tk.Entry(
            self.message_frame, 
            bg=self.colors["bg"], 
            fg=self.colors["fg"], 
            font=("Arial", 16)
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # Botón de enviar 
        self.send_button = tk.Button(
            self.message_frame, 
            text="Enviar", 
            bg=self.colors["accent"], 
            fg="#FFFFFF", 
            font=("Arial", 14), 
            command=self.send_message
        )
        self.send_button.pack(side="right", padx=5, pady=5)

    def display_message(self, message, sender="self"):
        """Muestra mensajes con formato mejorado: izquierda y multilínea."""
        self.chat_history.config(state="normal")

        # Definir un límite de ancho 
        message_width = int(self.chat_history.winfo_width() * 0.80)

        # Aplicar formato con salto de línea si es necesario
        wrapped_message = self.wrap_text(message, message_width)

        # Formato visual: Izquierda para todos los mensajes
        if sender == "self":
            formatted_message = f"{wrapped_message}\n"
        else:
            formatted_message = f"{sender}: {wrapped_message}\n"

        # Mostrar el mensaje con fuente más grande
        self.chat_history.insert("end", formatted_message, ("message_tag",))
        self.chat_history.config(state="disabled")
        self.chat_history.yview("end")

        # Aplicar estilo al texto (aumentar fuente y espaciado)
        self.chat_history.tag_configure("message_tag", font=("Arial", 16), lmargin1=10, lmargin2=10, spacing1=5)

    def wrap_text(self, text, max_width):
        """Divide el texto en múltiples líneas si supera el ancho máximo."""
        return '\n'.join(textwrap.wrap(text, width=50))

    def create_sidebar(self):
        """Menú lateral con botón inferior y área superior para el nombre de usuario."""
        self.sidebar = tk.Frame(self, bg=self.colors["menu"], width=200)
        self.sidebar.pack(side="left", fill="both", expand=True)

        # Área superior con nombre de usuario
        self.username_label = tk.Label(
            self.sidebar, 
            text="Unknown", 
            bg=self.colors["menu"], 
            fg=self.colors["menu_fg"], 
            font=("Arial", 16, "bold")
        )
        self.username_label.pack(pady=10)

        # Frame para alinear los botones al fondo
        self.sidebar_buttons_frame = tk.Frame(self.sidebar, bg=self.colors["menu"])
        self.sidebar_buttons_frame.pack(side="bottom", fill="x")

        # Botones individuales con control dinámico
        self.login_button = tk.Button(
            self.sidebar_buttons_frame, 
            text="Login", 
            bg=self.colors["menu"], 
            fg=self.colors["menu_fg"],
            command=self.login_action,
            font=("Arial", 12),
            relief="flat",
            activebackground=self.colors["accent"],
            activeforeground="#FFFFFF",
        )
        self.login_button.pack(fill="x", padx=5, pady=2)

        self.connect_button = tk.Button(
            self.sidebar_buttons_frame, 
            text="Conectar", 
            bg=self.colors["menu"], 
            fg=self.colors["menu_fg"],
            command=self.connect_action,
            font=("Arial", 12),
            relief="flat",
            activebackground=self.colors["accent"],
            activeforeground="#FFFFFF",
        )
        self.connect_button.pack(fill="x", padx=5, pady=2)

        # Demás botones del menú
        menu_buttons = [
            ("Ingresar otro cmd", self.other_cmd),
            ("Crear Canal", self.create_channel),
            ("Cambiar Nick", self.change_nick_action),
            ("Conectar Servidor", self.connect_another_server_action),
            ("Info Servidor", self.server_info_action),
            ("Lista Servidores", self.server_links_action),
            ("Salir", self.close),
        ]

        for text, command in menu_buttons:
            button = tk.Button(
                self.sidebar_buttons_frame,
                text=text,
                bg=self.colors["menu"],
                fg=self.colors["menu_fg"],
                font=("Arial", 12),
                command=command,
                relief="flat",
                activebackground=self.colors["accent"],
                activeforeground="#FFFFFF",
            )
            button.pack(fill="x", pady=2, padx=5)

        # Asegurar actualización de estado
        self.update_buttons()

    def create_info_chat_bar(self):
        """Cinta superior que muestra el canal o usuario activo."""
        self.status_chat_bar = tk.Frame(self.chat_frame, bg=self.colors["fg"])
        self.status_chat_bar.pack(fill="x")

        # Mostrar el canal/usuario seleccionado
        self.target_label = tk.Label(
            self.status_chat_bar, textvariable=self.active_target, fg="black", bg=self.colors["fg"], font=("Arial", 16, "bold")
        )
        self.target_label.pack(side="left", padx=10)

        # Botón para abrir el menú contextual
        self.options_button = tk.Button(
            self.status_chat_bar, 
            text="Opciones", 
            font=("Arial", 16),
            command=self.open_context_menu
        )
        self.options_button.pack(side="right", padx=10)

    def open_context_menu(self):
        """Despliega un menú con opciones para canales o usuarios."""
        target = self.active_target.get()
        if self.active_target_type == -1:
            # messagebox.showerror("Error", "Debes seleccionar un canal o usuario primero.")
            return

        # Menú emergente
        context_menu = tk.Toplevel(self)
        context_menu.title(f"Opciones para {target}")

        tk.Label(context_menu, text=f"Opciones para {target}").pack(pady=10)

        if self.active_target_type == 0:
            context_menu.geometry("300x370")
            current_topic = self.get_topic()
            self.channel_topic = tk.Label(
                context_menu, 
                text=current_topic, 
                font=("Arial", 14, "bold")
            )
            self.channel_topic.pack(pady=5)
            tk.Button(context_menu, text="Cambiar Tema", font=("Arial", 13), command=self.change_topic).pack(pady=5)
            tk.Button(context_menu, text="Expulsar Usuario", font=("Arial", 13), command=self.kick_user).pack(pady=5)
            tk.Button(context_menu, text="Invitar al Canal", font=("Arial", 13), command=self.invite_to_channel).pack(pady=5)
            tk.Button(context_menu, text="Cambiar Modo", font=("Arial", 13), command=self.change_mode).pack(pady=5)
            tk.Button(context_menu, text="Mostrar Usuarios", font=("Arial", 13), command=self.check_users).pack(pady=5)
            tk.Button(context_menu, text="Dejar Canal", font=("Arial",13), command=self.quit_channel).pack(pady=5)
        else:
            context_menu.geometry("300x200")
            # Obtener la info del usuario llamando al método
            self.get_user_info()
            tk.Label(context_menu, text=self.user_info, font=("Arial", 14, "bold")).pack(pady=5)
            tk.Button(context_menu, text="Cambiar Modo", font=("Arial", 13), command=self.change_mode).pack(pady=5)
            tk.Button(context_menu, text="Invita a un Canal", font=("Arial", 13), command=self.invite_user).pack(pady=5)


    def change_nick_action(self):
        if self.is_authenticated:
            x = True
            while(x):
                new_user = simpledialog.askstring("Cambiar Usuario", "Ingresa tu nuevo nombre de usuario:")
                
                if new_user:
                    def update_nick():
                        try:
                            # Actualiza el nombre de usuario en la GUI y envía el comando al servidor
                            self.username_label.config(text=f"{new_user}")
                            self.nick = new_user
                            if self.connection:
                                self.connection.nick(self.nick)
                            messagebox.showinfo("Usuario Actualizado", f"Nuevo nombre de usuario: {new_user}")
                        except Exception as e:
                            messagebox.showerror("Error", f"No se pudo cambiar el apodo: {e}")

                    # Ejecuta la actualización en un hilo separado
                    thread = threading.Thread(target=update_nick, daemon=True)
                    thread.start()
                    x = False
                else:
                    messagebox.showerror("Error", "Debes completar el campo")
        else:
            messagebox.showerror("Error", "Debes autenticarte primero") 
        
    def server_info_action(self):
        """Solicita y muestra la versión del servidor IRC."""
        if not self.connection:
            messagebox.showerror("Error", "No estás conectado al servidor.")
            return
        
        # Enviar el comando VERSION al servidor
        try:
            self.connection.version()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo solicitar la información del servidor: {e}")

        # # Crear una cola para almacenar la información del servidor
        # self.server_info_queue = queue.Queue()

        # def request_version():
        #     """Hilo para solicitar y procesar la versión del servidor."""
        #     try:
        #         # Solicita la versión del servidor
        #         self.connection.version()

        #         # # Procesa todas las líneas de respuesta
        #         # version_found = False
        #         # for response in self.connection.receive():
        #         #     if isinstance(response, tuple) and response[1] == "351":  # Código 351 para VERSION
        #         #         server_name = response[2][2]  # Nombre del servidor
        #         #         version_info = response[2][1]  # Versión del servidor
        #         #         self.server_info_queue.put((server_name, version_info))
        #         #         version_found = True
        #         #         break  # Una vez encontrada la versión, no seguimos procesando
        #         # if not version_found:
        #         #     self.server_info_queue.put(("Error", "No se pudo obtener la versión del servidor."))
        #     except Exception as e:
        #         self.server_info_queue.put(("Error", f"No se pudo obtener la información: {e}"))
        #     finally:
        #         self.server_info_queue.put(None)  # Fin de los datos

        # # Crear un hilo para la solicitud y el procesamiento
        # thread = threading.Thread(target=request_version, daemon=True)
        # thread.start()

        # # Actualizar la información en la interfaz
        # self.update_server_info()

    # def update_server_info(self):
    #     """Procesa la información del servidor desde la cola y actualiza la interfaz."""
    #     try:
    #         while not self.server_info_queue.empty():
    #             info = self.server_info_queue.get()
    #             if info is None:  # Fin de los datos
    #                 return

    #             # Desempaqueta y muestra la información
    #             server_name, version_info = info
    #             if server_name == "Error":
    #                 messagebox.showerror("Error", version_info)
    #             else:
    #                 messagebox.showinfo("Información", f"Servidor: {server_name}\nVersión: {version_info}")
    #     except Exception as e:
    #         print(f"Error actualizando la información del servidor: {e}")
    #     finally:
    #         # Vuelve a llamar a esta función después de 100 ms
    #         self.after(100, self.update_server_info)


    def server_links_action(self):
        """Solicita y muestra la lista de servidores conectados al IRC."""
        if not self.connection:
            messagebox.showerror("Error", "No estás conectado al servidor.")
            return

        # Enviar el comando LINKS al servidor
        try:
            self.connection.links()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo solicitar la lista de servidores: {e}")

    #     # Crear una cola para almacenar los datos del servidor
    #     self.server_links_queue = queue.Queue()

    #     def request_links():
    #         """Hilo para solicitar y procesar la lista de servidores."""
    #         try:
    #             # Solicita la lista de servidores
    #             self.connection.links()

    #             while True:
    #                 for response in self.connection.receive():
    #                     prefix, command, params, trailing = parse_message(response)

    #                     if command == "364":
    #                         server_name = prefix
    #                         description = trailing
    #                     # if isinstance(response, tuple) and response[1] == "364":  # Código 364 para LINKS
    #                     #     server_name = response[2][0]  # Nombre del servidor
    #                     #     description = response[3]  # Trailing contiene la descripción
    #                         self.server_links_queue.put(f"{server_name} - {description}")
    #                     elif command == "365":
    #                     # elif isinstance(response, tuple) and response[1] == "365":  # Fin de la lista de LINKS
    #                         break
    #         except Exception as e:
    #             self.server_links_queue.put(f"Error: {e}")
    #         finally:
    #             # Marca el final de los datos en la cola
    #             self.server_links_queue.put(None)

    #     # Crear un hilo para la solicitud y el procesamiento
    #     thread = threading.Thread(target=request_links, daemon=True)
    #     thread.start()

    #     # Crear la ventana para mostrar los servidores
    #     servers_window = tk.Toplevel(self)
    #     servers_window.title(f"Servidores conectados")
    #     servers_window.geometry("400x400")
    #     servers_window.configure(bg=self.colors["bg"])

    #     tk.Label(servers_window, text=f"Servidores conectados", font=("Arial", 16, "bold"),
    #             bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=10)

    #     # Frame para contener la lista y la barra de desplazamiento
    #     list_frame = tk.Frame(servers_window, bg=self.colors["bg"])
    #     list_frame.pack(fill="both", expand=True)

    #     scrollbar = tk.Scrollbar(list_frame)
    #     scrollbar.pack(side="right", fill="y")

    #     self.server_linksbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
    #                                     bg=self.colors["bg"], fg=self.colors["fg"], font=("Arial", 16))
    #     self.server_linksbox.pack(side="left", fill="both", expand=True)
    #     scrollbar.config(command=self.server_linksbox.yview)

    #     # Actualizar la lista de servidores periódicamente
    #     self.update_server_links()

    # def update_server_links(self):
    #     """Actualiza la lista de servidores desde la cola."""
    #     try:
    #         while not self.server_links_queue.empty():
    #             server = self.server_links_queue.get()
    #             if server is None:  # Fin de los datos
    #                 return
    #             self.server_linksbox.insert(tk.END, server)
    #     except Exception as e:
    #         print(f"Error actualizando lista de servidores: {e}")
    #     finally:
    #         # Vuelve a llamar a esta función después de 100 ms
    #         self.after(100, self.update_server_links)

    def close(self):
        self.disconnect_action
        self.quit

    def send_message(self):
        """Envía un mensaje al canal o usuario seleccionado."""
        target = self.active_target.get()  # El objetivo puede ser un canal o un usuario
        message = self.message_entry.get()  # Mensaje a enviar

        if not self.connection:
            messagebox.showerror("Error", "No estás conectado al servidor.")
            return

        if not message.strip():
            messagebox.showwarning("Mensaje vacío", "No puedes enviar un mensaje vacío.")
            return
        
        if target == "Servidor":
            messagebox.showwarning("mensaje a servidor", "No se le pueden pasar mensajes directos al servidor")
            return
        
        def send():
            try:
                if "Canal:" in target:
                    channel = target.split("Canal: ")[1]
                    self.connection.message(channel, message)  # Enviar al canal
                elif "Usuario:" in target:
                    user = target.split("Usuario: ")[1]
                    self.connection.message(user, message)  # Enviar al usuario
                else:
                    messagebox.showwarning("Sin destino", "Selecciona un canal o usuario.")
                    return

                # Actualizar la interfaz con el mensaje enviado
                self.display_message(f"Tú: {message}", sender="self")  # Mostrar el mensaje en el chat
                self.message_entry.delete(0, tk.END)

                # Guardar el mensaje en el historial
                if target not in self.message_history:
                    self.message_history[target] = []
                self.message_history[target].append(("self", message))  # Guardar el mensaje enviado

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo enviar el mensaje: {e}")

        # Ejecuta la lógica de envío en un hilo separado
        thread = threading.Thread(target=send, daemon=True)
        thread.start()


    def connect_action(self):
        """Solicitar servidor y puerto en un solo formulario."""
        if not self.is_authenticated:
            messagebox.showerror("Conectar", "Debes autenticarte primero")
            return
        
        connect_window = tk.Toplevel(self)
        connect_window.title("Conectar al Servidor")
        connect_window.geometry("300x200")

        tk.Label(connect_window, text="Servidor:").pack(pady=5)
        server_entry = tk.Entry(connect_window)
        server_entry.pack(pady=5)

        tk.Label(connect_window, text="Puerto:").pack(pady=5)
        port_entry = tk.Entry(connect_window)
        port_entry.pack(pady=5)

        def attempt_connection():
            server = server_entry.get()
            port = port_entry.get()
            if not server or not port:
                messagebox.showerror("Error", "Debes completar ambos campos.")
                return
            try:
                int(port)  # Verificar si es numérico
                self.connection = ClientConnection(server, port)

                # Registrar el cliente
                self.connection.connect_client(self.password, self.nick, self.username)
                
                # Conectar y procesar mensajes
                self.is_connected = True
                self.start_receiving()
                self.process_server_messages()  # Iniciar el procesamiento de mensajes
                self.update_connection_status(True)
                self.update_buttons()
                messagebox.showinfo("Conectado", f"Conectando a {server}:{port}...")
                connect_window.destroy()

            except ValueError:
                messagebox.showerror("Error", "El puerto debe ser un número.")

        connect_button = tk.Button(connect_window, text="Conectar", command=attempt_connection)
        connect_button.pack(pady=10)
        
    def connect_another_server_action(self):
        """Solicitar servidor y puerto para enlazar otro servidor mediante el comando CONNECT."""
        if not self.is_connected:
            messagebox.showerror("Conectar", "Debe estar conectado para poder enlazar otro servidor.")
            return

        # Crear la ventana para ingresar el servidor y el puerto
        connect_window = tk.Toplevel(self)
        connect_window.title("Conectar otro Servidor")
        connect_window.geometry("300x200")

        tk.Label(connect_window, text="Servidor:").pack(pady=5)
        server_entry = tk.Entry(connect_window)
        server_entry.pack(pady=5)

        tk.Label(connect_window, text="Puerto:").pack(pady=5)
        port_entry = tk.Entry(connect_window)
        port_entry.pack(pady=5)

        def attempt_connection():
            """Procesa los datos ingresados y envía el comando CONNECT."""
            server = server_entry.get().strip()
            port = port_entry.get().strip()

            if not server or not port:
                messagebox.showerror("Error", "Debes completar ambos campos.")
                return

            try:
                # Verificar que el puerto sea un número válido
                port = int(port)
            except ValueError:
                messagebox.showerror("Error", "El puerto debe ser un número.")
                return

            def execute_connect():
                """Ejecuta el comando CONNECT en un hilo separado."""
                try:
                    # Enviar el comando CONNECT al servidor
                    self.connection.send("CONNECT", [server, str(port)])
                    messagebox.showinfo("Éxito", f"Solicitud enviada para conectar a {server}:{port}.")
                    connect_window.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo conectar a {server}:{port}: {e}")

            # Ejecutar el comando en un hilo separado
            thread = threading.Thread(target=execute_connect, daemon=True)
            thread.start()

        connect_button = tk.Button(connect_window, text="Conectar", command=attempt_connection)
        connect_button.pack(pady=10)

    def disconnect_action(self):
        """Desconectarse y actualizar el estado."""
        if self.connection:
            try:
                self.is_connected = False  # Detener hilos de recepción
                self.connection.quit("Desconexión")
            except Exception as e:
                print(f"Error al enviar QUIT: {e}")
            finally:
                try:
                    self.connection.close()  # Cerrar socket
                except Exception as e:
                    print(f"Error al cerrar conexión: {e}")
                self.connection = None  # Eliminar referencia
                
                # Limpiar UI y datos
                self.message_history.clear()
                self.channels = {"Servidor": {"topic": "Mensajes del servidor"}}
                self.all_users.clear()
                self.channel_list.delete(0, tk.END)
                self.user_list.delete(0, tk.END)
                self.update_connection_status(False)
                self.update_buttons()
                messagebox.showinfo("Desconectado", "Conexión cerrada.")
        else:
            messagebox.showwarning("Desconexión", "No estás conectado a ningún servidor.")
    
    def logout_action(self):
        """Cerrar sesión y reiniciar los datos."""
        if messagebox.askyesno("Cerrar sesión", "¿Seguro que quieres cerrar sesión?"):
            if self.is_connected:
                self.disconnect_action()  # Desconecta antes de cerrar sesión si se está conectado
            self.username_label.config(text="Unknown")
            self.is_authenticated = False
            self.update_buttons()
            messagebox.showinfo("Sesión Cerrada", "Te has deslogueado correctamente.")

    def login_action(self):
        """Acción de autenticación restringida a una vez."""
        if self.is_authenticated:
            messagebox.showwarning("Ya autenticado", "Ya has autenticado un usuario. Usa 'Logout'.")
            return

        login_window = tk.Toplevel(self)
        login_window.title("Autenticación")
        login_window.geometry("300x200")

        # Entradas de datos
        tk.Label(login_window, text="Nombre de usuario:").pack(pady=5)
        username_entry = tk.Entry(login_window)
        username_entry.pack(pady=5)

        tk.Label(login_window, text="Contraseña:").pack(pady=5)
        password_entry = tk.Entry(login_window, show="*")
        password_entry.pack(pady=5)

        def save_user_data():
            username = username_entry.get()
            password = password_entry.get()
            if username and password:
                self.username_label.config(text=f"{username}")
                self.username=username
                self.nick=username
                self.password=password
                self.is_authenticated = True
                self.update_buttons()  # Llamada a actualización de botones
                messagebox.showinfo("Autenticación", f"Bienvenido, {username}")
                login_window.destroy()
            else:
                messagebox.showerror("Error", "Debes completar ambos campos")

        submit_button = tk.Button(login_window, text="Guardar", command=save_user_data)
        submit_button.pack(pady=10)

    def update_buttons(self):
        """Actualiza dinámicamente los textos y comandos de los botones."""
        # Actualización de Login/Logout
        if self.is_authenticated:
            self.login_button.config(text="Logout", command=self.logout_action)
        else:
            self.login_button.config(text="Login", command=self.login_action)

        # Actualización de Conectar/Desconectar
        if self.is_connected:
            self.connect_button.config(text="Desconectar", command=self.disconnect_action)
        else:
            self.connect_button.config(text="Conectar", command=self.connect_action)

    def update_active_target(self, event):
        """Actualiza la cinta superior con el canal o usuario seleccionado."""
        selected_tab = self.tabs.index(self.tabs.select())  # 0 = Canales, 1 = Usuarios
        if selected_tab == 0:  # Canales
            selection = self.channel_list.curselection()
            if selection:
                selected_channel = self.channel_list.get(selection[0])
                self.active_target.set(f"Canal: {selected_channel}")
                self.active_target_type = 0

        elif selected_tab == 1:  # Usuarios
            selection = self.user_list.curselection()
            if selection:
                selected_user = self.user_list.get(selection[0])
                self.active_target.set(f"Usuario: {selected_user}")
                self.active_target_type = 1
        else:
            self.active_target.set("Servidor")
            self.active_target_type = -1

        # Limpiar el historial de chat actual
        self.chat_history.config(state="normal")
        self.chat_history.delete(1.0, tk.END)
        
        # Limpiar indicador de nuevos mensajes
        target = self.active_target.get().replace(" *", "")
        if target in self.new_message_indicators:
            self.new_message_indicators[target] = False
            self.update_list_item(target, False)

        # Mostrar mensajes del historial para el canal/usuario seleccionado
        if target in self.message_history:
            for sender, message in self.message_history[target]:
                self.display_message(message, sender)

        self.chat_history.config(state="disabled")

    def change_mode(self):
        """Solicita el modo a establecer y lo aplica a un canal, un usuario o un usuario dentro de un canal."""
        try:
            # Determinar si el objetivo es un canal, un usuario o ambos
            target = self.active_target.get()
            if "Canal:" in target:
                target_type = "canal"
                target_name = target.split("Canal: ")[1]
            elif "Usuario:" in target:
                target_type = "usuario"
                target_name = target.split("Usuario: ")[1]
            else:
                messagebox.showerror("Error", "Debes seleccionar un canal o un usuario.")
                return
        except IndexError:
            messagebox.showerror("Error", "El formato del objetivo no es válido.")
            return

        # Solicitar el modo a establecer
        if target_type == "canal":
            mode = simpledialog.askstring("Establecer modo", f"Ingrese el modo a establecer para el canal {target_name}:")
            if not mode:
                return  # Si el usuario cancela el diálogo
            user = None  # No aplica usuario si es solo para el canal
        elif target_type == "usuario":
            # Solicitar el canal y el modo si el objetivo es un usuario
            channel = simpledialog.askstring("Establecer modo", "Ingresa el canal donde aplicar el modo:")
            if not channel:
                return  # Si el usuario cancela el diálogo
            mode = simpledialog.askstring("Establecer modo", f"Ingrese el modo a establecer para el usuario {target_name} en el canal {channel}:")
            if not mode:
                return  # Si el usuario cancela el diálogo
            user = target_name
            target_name = channel  # El canal se convierte en el target principal

        def execute_change_mode():
            """Ejecuta el comando MODE en un hilo separado."""
            try:
                if user:
                    # Modo aplicado a un usuario dentro de un canal
                    self.connection.change_mode(target_name, mode + " " + user)
                else:
                    # Modo aplicado al canal
                    self.connection.change_mode(target_name, mode)

                target_description = f"{user} en {target_name}" if user else target_name
                messagebox.showinfo("Éxito", f"Modo '{mode}' establecido para {target_description}.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo establecer el modo: {e}")

        # Crear un hilo para ejecutar el comando
        thread = threading.Thread(target=execute_change_mode, daemon=True)
        thread.start()



    def change_topic(self):
        """Muestra un cuadro de diálogo para cambiar el tema del canal."""
        try:
            target = self.active_target.get()
            channel = target.split("Canal: ")[1]
        except IndexError:
            messagebox.showerror("Error", "Debes seleccionar un canal.")
            return

        # Solicitar el nuevo tema
        topic = simpledialog.askstring("Cambiar tema", "Ingresa el nuevo tema:")
        if topic is None:  # Si el usuario cancela el diálogo
            return

        def execute_change_topic():
            """Ejecuta el comando TOPIC en un hilo separado."""
            try:
                self.connection.change_topic(channel, topic)  # Enviar el comando TOPIC al servidor
                self.channel_topic.config(text=f"{topic}")  # Actualizar la interfaz gráfica
                self.channels[channel] = {"topic": topic}
                messagebox.showinfo("Éxito", f"El tema del canal {channel} ha sido actualizado.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cambiar el tema: {e}")
            finally:
                self.channels[channel] = {"Topic": topic}

        # Crear un hilo para ejecutar el comando
        thread = threading.Thread(target=execute_change_topic, daemon=True)
        thread.start()


    def invite_to_channel(self):
        """Solicita el nombre de un usuario y envía una invitación para unirse al canal activo."""
        try:
            # Obtener el canal activo
            channel = self.active_target.get().split("Canal: ")[1]
        except IndexError:
            messagebox.showerror("Error", "Debes seleccionar un canal.")
            return

        # Solicitar el nombre del usuario a invitar
        target = simpledialog.askstring("Extender invitación", "Ingresa el nombre del usuario:")
        if not target:
            return  # Si el usuario cancela el diálogo, no hace nada

        def execute_invite():
            """Ejecuta el comando INVITE en un hilo separado."""
            try:
                self.connection.invite(target, channel)  # Enviar el comando INVITE
                messagebox.showinfo("Notificación", f"Invitación enviada a {target} para unirse al canal {channel}.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo enviar la invitación: {e}")

        # Crear un hilo para ejecutar el comando
        thread = threading.Thread(target=execute_invite, daemon=True)
        thread.start()


    def invite_user(self):
        """Solicita el canal y envía una invitación a un usuario fijo."""
        try:
            # Obtener el usuario activo
            user = self.active_target.get().split("Usuario: ")[1]
        except IndexError:
            messagebox.showerror("Error", "Debes seleccionar un usuario.")
            return

        # Solicitar el canal donde invitar al usuario
        channel = simpledialog.askstring("Extender invitación", f"Ingrese el nombre del canal para invitar a {user}:")
        if not channel:
            return  # Si el usuario cancela el diálogo

        def execute_invite():
            """Ejecuta el comando INVITE en un hilo separado."""
            try:
                self.connection.invite(user, channel)  # Enviar el comando INVITE
                messagebox.showinfo("Notificación", f"Invitación enviada a {user} para unirse al canal {channel}.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo enviar la invitación: {e}")

        # Crear un hilo para ejecutar el comando
        thread = threading.Thread(target=execute_invite, daemon=True)
        thread.start()


    def kick_user(self):
        """Muestra una ventana para expulsar a un usuario de un canal."""
        try:
            channel = self.active_target.get().split("Canal: ")[1]
        except IndexError:
            messagebox.showerror("Error", "Debes seleccionar un canal.")
            return

        kick_window = tk.Toplevel(self)
        kick_window.title("Expulsar usuario")
        kick_window.geometry("300x200")

        # Entradas de datos
        tk.Label(kick_window, text="Nombre del usuario:").pack(pady=5)
        username_entry = tk.Entry(kick_window)
        username_entry.pack(pady=5)

        tk.Label(kick_window, text="Razón (opcional):").pack(pady=5)
        reason_entry = tk.Entry(kick_window)
        reason_entry.pack(pady=5)

        def call_command():
            """Ejecuta el comando KICK en un hilo separado."""
            user = username_entry.get().strip()
            reason = reason_entry.get().strip()

            if not user:
                messagebox.showerror("Error", "El nombre del usuario no puede estar vacío.")
                return

            def execute_kick():
                try:
                    self.connection.kick(channel, user, reason if reason else "Expulsado")  # Comando KICK
                    messagebox.showinfo("Éxito", f"Usuario {user} expulsado del canal {channel}.")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo expulsar al usuario: {e}")

            # Crear un hilo para ejecutar el comando
            thread = threading.Thread(target=execute_kick, daemon=True)
            thread.start()

        submit_button = tk.Button(kick_window, text="Expulsar", command=call_command)
        submit_button.pack(pady=10)

    # def check_users(self):
    #     """Solicita y muestra la lista de usuarios en un canal usando el comando NAMES."""
    #     try:
    #         # Obtener el canal activo
    #         channel = self.active_target.get().split("Canal: ")[1]
    #     except IndexError:
    #         messagebox.showerror("Error", "Debes seleccionar un canal.")
    #         return

    #     # Crear una cola para almacenar los usuarios del canal
    #     self.users_queue = queue.Queue()

    #     def request_names():
    #         """Hilo para solicitar y procesar la lista de usuarios del canal."""
    #         try:
    #             # Enviar el comando NAMES al servidor
    #             self.connection.names(channel)

    #             # Procesar todas las líneas de respuesta
    #             users = []
    #             for response in self.connection.receive():
    #                 if isinstance(response, tuple) and response[1] == "353":  # Código 353 para NAMES
    #                     # Los usuarios están en el trailing (última parte del mensaje)
    #                     users_in_line = response[3].split()
    #                     users.extend(users_in_line)
    #                 elif isinstance(response, tuple) and response[1] == "366":  # Fin de NAMES
    #                     break

    #             # Pasar la lista de usuarios a la cola
    #             for user in users:
    #                 self.users_queue.put(user)
    #             self.users_queue.put(None)  # Fin de los datos
    #         except Exception as e:
    #             self.users_queue.put(f"Error: {e}")
    #             self.users_queue.put(None)  # Fin de los datos en caso de error

    #     # Crear un hilo para ejecutar la solicitud
    #     thread = threading.Thread(target=request_names, daemon=True)
    #     thread.start()

    #     # Mostrar la ventana con los usuarios
    #     self.display_users_window(channel)

    # def display_users_window(self, channel):
    #     """Muestra una ventana con la lista de usuarios del canal."""
    #     users_window = tk.Toplevel(self)
    #     users_window.title(f"Usuarios en {channel}")
    #     users_window.geometry("300x400")
    #     users_window.configure(bg=self.colors["bg"])

    #     tk.Label(users_window, text=f"Usuarios en {channel}", font=("Arial", 16, "bold"),
    #             bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=10)

    #     # Frame para contener la lista y la barra de desplazamiento
    #     list_frame = tk.Frame(users_window, bg=self.colors["bg"])
    #     list_frame.pack(fill="both", expand=True)

    #     # Barra de desplazamiento
    #     scrollbar = tk.Scrollbar(list_frame)
    #     scrollbar.pack(side="right", fill="y")

    #     # Listbox para mostrar usuarios
    #     user_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
    #                             bg=self.colors["bg"], fg=self.colors["fg"], font=("Arial", 14))
    #     user_listbox.pack(side="left", fill="both", expand=True)
    #     scrollbar.config(command=user_listbox.yview)

    #     # Actualizar la lista de usuarios desde la cola
    #     def update_users():
    #         try:
    #             while not self.users_queue.empty():
    #                 user = self.users_queue.get()
    #                 if user is None:  # Fin de los datos
    #                     return
    #                 elif isinstance(user, str) and user.startswith("Error:"):
    #                     messagebox.showerror("Error", user[7:])
    #                 else:
    #                     user_listbox.insert(tk.END, user)
    #         except Exception as e:
    #             print(f"Error actualizando la lista de usuarios: {e}")
    #         finally:
    #             self.after(100, update_users)

    #     update_users()

    def check_users(self):
        """Solicita la lista de usuarios en un canal usando el comando NAMES."""
        try:
            # Obtener el canal activo
            channel = self.active_target.get().split("Canal: ")[1]
        except IndexError:
            messagebox.showerror("Error", "Debes seleccionar un canal.")
            return

        # Enviar el comando NAMES al servidor
        try:
            self.connection.names(channel)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo solicitar la lista de usuarios: {e}")


    def get_topic(self):
        """Obtiene el tema del canal activo."""
        target = self.active_target.get()
        # Si el target es "Canal: #nombre", extrae solo el nombre
        if "Canal: " in target:
            channel = target.split("Canal: ")[1]
            return self.channels.get(channel, {}).get("topic", "Sin tema")
        return "Sin tema"

    # def get_topic(self):
    #     """Solicita el tema del canal usando el comando TOPIC."""
    #     try:
    #         channel = self.active_target.get()
    #         self.connection.change_topic(channel)
    #     except Exception as e:
    #         messagebox.showerror("Error", f"No se pudo solicitar el tema del canal: {e}")

    # def get_user_info(self):
    #     """Obtiene la información del usuario usando WHOIS."""
    #     target = self.active_target.get()
    #     if "Usuario: " in target:
    #         user = target.split("Usuario: ")[1]
    #         self.whois_user(user)  # Ejecuta el comando WHOIS
    #         return self.user_info if hasattr(self, 'user_info') else "Información no disponible"
    #     return "Selecciona un usuario"

    def get_user_info(self):
        """Solicita la información de un usuario usando WHOIS."""
        target = self.active_target.get()
        if "Usuario: " in target:
            user = target.split("Usuario: ")[1]
            try:
                self.connection.whois(user)  # Enviar el comando WHOIS
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo solicitar la información del usuario: {e}")
        else:
            messagebox.showwarning("Error", "Selecciona un usuario primero.")

    def other_cmd(self):
        """
        Abre una ventana para permitir la entrada de comandos IRC personalizados.
        """
        command_window = tk.Toplevel(self)
        command_window.title("Comandos")
        command_window.geometry("500x400")

        # Entradas de datos
        tk.Label(command_window, text="Ingrese una línea de comandos:").pack(pady=5)
        command_entry = tk.Entry(command_window, width=50)
        command_entry.pack(pady=5)

        def process():
            """Procesa el comando ingresado y lo envía al servidor."""
            command = command_entry.get().strip()
            if not self.connection:
                messagebox.showerror("Error", "No estás conectado al servidor.")
                return

            if not command:
                messagebox.showerror("Error", "El comando no puede estar vacío.")
                return

            if command in ["USER", "PASS", "NICK", "VERSION", "QUIT", "KICK", "JOIN", "PART", "MODE", "TOPIC", "NAMES", "LIST", "INVITE", "PRIVSMG", "WHO", "WHOIS"]:
                messagebox.showwarning("Inválido", f"El comando {command}, no está siendo procesado por esta vía")
                return

            def send_command():
                try:
                    # Divide el comando en partes: comando, parámetros y trailing
                    parts = command.split(" ", 1)
                    irc_command = parts[0].upper()  # Comando en mayúsculas
                    params_and_trailing = parts[1] if len(parts) > 1 else None

                    # Separa parámetros de trailing (si existe)
                    if params_and_trailing and ":" in params_and_trailing:
                        params, trailing = params_and_trailing.split(":", 1)
                        params = params.strip().split()
                    else:
                        params = params_and_trailing.split() if params_and_trailing else []
                        trailing = None

                    # Enviar el comando al servidor
                    print(f"Enviando comando: {irc_command}, Params: {params}, Trailing: {trailing}")  # Depuración
                    self.connection.send(irc_command, params, trailing)
                    messagebox.showinfo("Comando enviado", f"Comando enviado: {command}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo enviar el comando: {e}")

            # Enviar en un hilo separado
            thread = threading.Thread(target=send_command, daemon=True)
            thread.start()

        def show_cmd_list():
            """Muestra una lista de comandos ejecutables con su estructura."""
            command_list = [
                # "PASS <password>", 
                # "USER <username> <hostname> <servername> <realname>",
                # "NICK <nickname>", 
                "OPER <name> <password>", 
                # "QUIT [<message>]",
                "SQUIT <server> [<message>]", 
                "SERVICE <name> <reserved> <distribution> <type> <reserved> <info>",
                # "JOIN <channel>{,<channel>}", 
                # "PART <channel>{,<channel>} [<message>]",
                # "MODE <target> <flags> [<parameters>]", 
                # "TOPIC <channel> [<new_topic>]",
                # "NAMES [<channel>{,<channel>}]", 
                # "LIST [<channel>{,<channel>}]", 
                # "INVITE <nickname> <channel>",
                # "KICK <channel> <user> [<message>]", 
                "MOTD", 
                "LUSERS", 
                # "VERSION", 
                "STATS",
                # "LINKS", 
                "TIME", 
                "CONNECT <target_server> <port>", 
                "SERVLIST [<mask>]",
                "SQUERY <service_name> <text>", 
                "TRACE", 
                "ADMIN", 
                "INFO",
                # "PRIVMSG <target> <message>", 
                "NOTICE <target> <message>", 
                # "WHO [<mask>]",
                # "WHOIS <nickname>{,<nickname>}", 
                "WHOWAS <nickname>{,<nickname>}",
                "PING <server>", 
                "PONG <server>", 
                "AWAY [<message>]", 
                "REHASH",
                "DIE", 
                "RESTART", 
                "ERROR <message>", 
                "KILL <nickname> <message>",
                "SUMMON <nickname> [<server>]", 
                "USERS [<server>]", 
                "WALLOPS <message>",
                "USERHOST <nickname>{<nickname>}", 
                "ISON <nickname>{<nickname>}"
            ]
            cmd_list_window = tk.Toplevel(command_window)
            cmd_list_window.title("Comandos ejecutables")
            cmd_list_window.geometry("500x500")

            tk.Label(cmd_list_window, text="Comandos IRC soportados:", font=("Arial", 12, "bold")).pack(pady=10)
            cmd_listbox = tk.Listbox(cmd_list_window, bg="#f0f0f0", font=("Arial", 10))
            cmd_listbox.pack(fill="both", expand=True, padx=10, pady=10)

            for cmd in command_list:
                cmd_listbox.insert(tk.END, cmd)

        # Botones
        submit_button = tk.Button(command_window, text="Enviar", command=process)
        submit_button.pack(pady=10)

        cmd_list_button = tk.Button(command_window, text="Comandos ejecutables", command=show_cmd_list)
        cmd_list_button.pack(pady=10)


    def quit_channel(self):
        channel = self.active_target.split("Canal: ")[1]
        self.connection.part_channel(channel)
        self.active_target = tk.StringVar(value="Ninguno seleccionado")
        

    def signal_new_message(self, target):
        """Señaliza que hay nuevos mensajes en el canal/usuario/servidor."""
        if target not in self.new_message_indicators:
            self.new_message_indicators[target] = True

        # Actualizar solo el elemento específico en la lista
        if target == "servidor":
            self.update_list_item("Servidor", self.new_message_indicators["servidor"])
        else:
            self.update_list_item(target, self.new_message_indicators[target])

    def update_list_item(self, item, has_new_message):
        """Actualiza un elemento específico en la lista de canales o usuarios."""
        # Buscar el elemento en la lista de canales
        for i in range(self.channel_list.size()):
            if self.channel_list.get(i).replace(" *", "") == item:
                display_name = item
                if has_new_message:
                    display_name += " *"
                self.channel_list.delete(i)
                self.channel_list.insert(i, display_name)
                return

        # Buscar el elemento en la lista de usuarios
        for i in range(self.user_list.size()):
            if self.user_list.get(i).replace(" *", "") == item:
                display_name = item
                if has_new_message:
                    display_name += " *"
                self.user_list.delete(i)
                self.user_list.insert(i, display_name)
                return     

    def request_channel_list(self):
        """Solicita la lista de canales (comando LIST)."""
        def execute_list():
            try:
                self.connection.list()
                threading.Thread(target=self.process_list_responses, daemon=True).start()
            except Exception as e:
                print(f"Error al solicitar lista de canales: {e}")
        threading.Thread(target=execute_list, daemon=True).start()
 
    def process_list_responses(self):
        """Procesa respuestas del comando LIST."""
        while True:
            try:                
                # raw_response = self.server_messages.get(timeout=1)
                raw_response = self.channel_list_queue.get(timeout=1)
                prefix, command, params, trailing = parse_message(raw_response)
            
                if command == "322":  # LIST
                    channel = params[1] if len(params) > 1 else params[0]
                    # Separar modos y tema (ej: "[+nt] Tema real" -> "Tema real")
                    topic = trailing.split("]", 1)[-1].strip() if "]" in trailing else trailing
                    self.channels[channel] = {"topic": topic}   
                elif command == "323":  # Fin de LIST
                    break

            except queue.Empty:
                continue

    def request_user_list(self):
        """Solicita la lista global de usuarios (comando WHO)."""
        def execute_who():
            try:
                self.connection.who("*")
                threading.Thread(target=self.process_who_responses, daemon=True).start()
            except Exception as e:
                print(f"Error al solicitar usuarios: {e}")
        threading.Thread(target=execute_who, daemon=True).start()

    def process_who_responses(self):
        """Procesa respuestas del comando WHO."""
        while True:
            try:
                # raw_response = self.server_messages.get(timeout=1)
                raw_response = self.user_list_queue.get(timeout=1)
                prefix, command, params, trailing = parse_message(raw_response)
            
                if command == "352":  # WHO
                    user = params[5]  # Nombre de usuario
                    self.all_users.add(user)
                elif command == "315":  # Fin de WHO
                    break
            except queue.Empty:
                continue

    # def whois_user(self, nick):
    #     """Solicita información detallada de un usuario y actualiza self.user_info."""
    #     def execute_whois():
    #         try:
    #             self.connection.whois(nick)
    #             while True:
    #                 try:
    #                     response = self.server_messages.get(timeout=1)
    #                     prefix, command, params, trailing = parse_message(response)
    #                     if command == "311":  # WHOIS respuesta
    #                         username = params[1]
    #                         realname = trailing
    #                         self.user_info = f"Usuario: {username}\nNombre real: {realname}"
    #                     elif command == "318":  # Fin de WHOIS
    #                         break
    #                 except queue.Empty:
    #                     continue
    #         except Exception as e:
    #             self.user_info = f"Error al obtener información: {e}"
    #     threading.Thread(target=execute_whois, daemon=True).start()


    def start_auto_updates(self):
        """Inicia la carga inicial y actualizaciones periódicas de canales/usuarios."""
        if self.is_connected and self.nick:  # Esperar hasta tener nick
            threading.Thread(target=self.request_channel_list, daemon=True).start()
            threading.Thread(target=self.request_user_list, daemon=True).start()
            
            # Obtener la lista actual de canales y usuarios
            current_channels = set(self.channel_list.get(0, tk.END))  # Obtener todos los canales del Listbox
            current_users = set(self.user_list.get(0, tk.END))  # Obtener todos los usuarios del Listbox

            # Eliminar usuarios que ya no están en el servidor
            for user in list(self.all_users):
                if user not in current_users and user != "Servidor":
                    self.all_users.remove(user)

            # Eliminar canales que ya no existen
            for channel in list(self.channels.keys()):
                if channel not in current_channels and channel != "Servidor":
                    del self.channels[channel]

            # Limpiar interfaz
            self.channel_list.delete(0, tk.END)
            self.user_list.delete(0, tk.END)

            # Agregar elementos de las listas
            for channel, topic in self.channels.items():
                self.channel_list.insert(tk.END, channel)

            for user in self.all_users:
                self.user_list.insert(tk.END, user)


        self.after(60000, self.start_auto_updates)

    def process_server_messages(self):
        """Procesa los mensajes del servidor desde la cola."""
        handled_commands = {
            "PRIVMSG", "NOTICE", "NICK" # Manejados en display_message
            # "001", "002", "003", "004", "005",  # Comandos de registro
            # "251", "252", "253", "254", "255", "265", "266",  # Estadísticas
            # "375", "372", "376",  # MOTD
            "322", "323", "315", "352", "311", "318", "364", "365", "351", "353", "366"  # Listas
        }

        while not self.server_messages.empty():
            try:
                raw_message = self.server_messages.get()
                
                prefix, command, params, trailing = parse_message(raw_message)
                display_text = f"{prefix} {command} {' '.join(params)} :{trailing}"

                print(f"prefix: {prefix}, command: {command}, params: {params}, trailing: {trailing}")

                print(f"[DEBUG] Comando: {command}, Params: {params}, Trailing: {trailing}")  # Depuración

                # Redirigir respuestas específicas a colas dedicadas
                if command in ["322", "323"]:  # Respuestas de LIST
                    self.channel_list_queue.put(raw_message)
                elif command in ["352", "315"]:  # Respuestas de WHO
                    self.user_list_queue.put(raw_message)

                # Manejar la respuesta del comando VERSION (código 351)
                elif command == "351":  # Respuesta de VERSION
                    server_name = params[2]  # Nombre del servidor
                    version_info = params[1]  # Versión del servidor
                    self.after(0, self._show_server_info, server_name, version_info)  # Mostrar en UI

                # Manejar la respuesta del comando LINKS
                elif command == "364":  # Respuesta de LINKS (servidor)
                    server_name = prefix  # El nombre del servidor está en el prefijo
                    description = trailing  # La descripción está en el trailing
                    self._add_server_link(server_name, description)  # Añadir a la lista

                elif command == "365":  # Fin de la lista de LINKS
                    self.after(0, self._show_server_links)  # Mostrar la lista en UI# Manejar la respuesta del comando NAMES
                
                if command == "353":  # Respuesta de NAMES (usuarios en un canal)
                    channel = params[2]  # El canal está en params[2]
                    users = trailing.split()  # Los usuarios están en el trailing
                    self._add_channel_users(channel, users)  # Añadir a la lista

                elif command == "366":  # Fin de la lista de NAMES
                    channel = params[1]  # El canal está en params[1]
                    self.after(0, self._show_channel_users, channel)  # Mostrar la lista en UI

                # Comando de inicio del servidor
                if command == "001":  # Registro exitoso
                    self.nick = params[0]
                    self.username_label.config(text=self.nick)
                    # Añadir el propio nick a la lista de usuarios
                    self.all_users.add(self.nick)
                    self.user_list.insert(tk.END, self.nick)
                    self.start_auto_updates()  # Iniciar carga de listas

                # Manejar la respuesta del comando WHOIS
                if command == "311":  # Respuesta de WHOIS (información del usuario)
                    username = params[1]  # Nombre de usuario
                    realname = trailing  # Nombre real
                    self.user_info = f"Usuario: {username}\nNombre real: {realname}"

                elif command == "318":  # Fin de WHOIS
                    continue
                #     if hasattr(self, "user_info"):
                #         self.after(0, self._show_user_info)  # Mostrar la información en UI
                #     else:
                #         self.after(0, messagebox.showinfo, "Información del Usuario", "No se encontró información.")
                        
                # # Manejar la respuesta del comando WHOIS (311)
                # if command == "311":  # WHOIS respuesta
                #     username = params[1]  # Nombre de usuario
                #     realname = trailing  # Nombre real
                #     self.context_menu_info = f"Usuario: {username}\nNombre real: {realname}"
                #     self.after(0, self._update_context_menu)  # Actualizar el menú contextual

                # # Manejar la respuesta del comando TOPIC (332)
                # if command == "332":  # TOPIC respuesta
                #     channel = params[1]  # Canal
                #     topic = trailing  # Tema del canal
                #     # self.context_menu_info = f"Tema del canal {channel}: {topic}"
                #     self.current_topic = f"Tema del canal {channel}: {topic}"
                #     # self.after(0, self._update_context_menu)  # Actualizar el menú contextual


                # Manejar cambio de nick (NICK)
                if command == "NICK":
                    old_nick = prefix.split('!')[0] if '!' in prefix else prefix
                    print(old_nick)
                    new_nick = trailing    #.strip()
                    print(new_nick)
                    
                    # Actualizar lista de usuarios
                    if old_nick in self.all_users:
                        self.all_users.remove(old_nick)
                        self.all_users.add(new_nick)
                    
                    # Actualizar interfaz
                    self.user_list.delete(0, tk.END)
                    for user in self.all_users:
                        self.user_list.insert(tk.END, user)
                    
                    # Actualizar historial de mensajes
                    for target in list(self.message_history.keys()):
                        updated_messages = []
                        for sender, msg in self.message_history[target]:
                            if sender == old_nick:
                                updated_messages.append((new_nick, msg))
                            else:
                                updated_messages.append((sender, msg))
                        self.message_history[target] = updated_messages
                    
                    # Actualizar target activo si es afectado
                    current_target = self.active_target.get()
                    if current_target == f"Usuario: {old_nick}":
                        self.active_target.set(f"Usuario: {new_nick}")
                        self.update_active_target()  # Forzar actualización de la interfaz

                # Comandos PRIVMSG/NOTICE (manejo especial)
                if command in ["PRIVMSG", "NOTICE"]:
                    if not params:
                        continue
                    target = params[0]
                    sender = prefix.split('!')[0] if '!' in prefix else "Servidor"
                    
                    # Actualizar historial y notificaciones
                    if target not in self.message_history:
                        self.message_history[target] = []
                    self.message_history[target].append((sender, trailing))
                    self.new_message_indicators[target] = True

                    # Actualizar UI si es el target activo
                    if target == self.active_target.get():
                        self.display_message(trailing, sender)
                    else:
                        self.signal_new_message(target)

                # Todos los demás comandos van al historial del servidor
                elif command not in handled_commands:
                    if "Servidor" not in self.message_history:
                        self.message_history["Servidor"] = []
                    self.message_history["Servidor"].append(("Servidor", display_text))
                    self.new_message_indicators["Servidor"] = True

                    if self.active_target.get() == "Servidor":
                        self.display_message(display_text, "Servidor")
                    else:
                        self.signal_new_message("Servidor")

            except IndexError as e:
                print(f"Error de índice en mensaje: {raw_message}")
            except Exception as e:
                print(f"Error crítico procesando mensaje: {str(e)}")
                import traceback
                traceback.print_exc()

        self.after(100, self.process_server_messages)

    def create_channel(self):
        channel = simpledialog.askstring("Crear Canal", "Nombre del canal (ej. #general):")
        if channel:

            if ' ' in channel:  # Validar espacios
                messagebox.showerror("Error", "¡Nombre inválido! Los canales no pueden contener espacios.")
                return 
        
            if not channel.startswith("#"):
                channel = f"#{channel}"  
            
            if len(channel) > 64:
                messagebox.showerror("Error", "Nombre inválido. Debe tener ≤64 caracteres.")
                return
            
            threading.Thread(target=self.connection.join_channel, args=(channel,), daemon=True).start()

            self.channels[channel] = {"topic": "sin definir"}
            self.channel_list.insert(tk.END, channel)

    def _show_server_info(self, server_name, version_info):
        """Muestra la información del servidor en un cuadro de diálogo."""
        messagebox.showinfo("Información del Servidor", f"Servidor: {server_name}\nVersión: {version_info}")

    def _add_server_link(self, server_name, description):
        """Añade un servidor a la lista temporal de servidores."""
        if not hasattr(self, "temp_server_links"):
            self.temp_server_links = []  # Lista temporal para almacenar servidores
        self.temp_server_links.append(f"{server_name} - {description}")

    def _show_server_links(self):
        """Muestra la lista de servidores en una ventana emergente."""
        if not hasattr(self, "temp_server_links") or not self.temp_server_links:
            messagebox.showinfo("Servidores Conectados", "No se encontraron servidores.")
            return

        # Crear la ventana para mostrar los servidores
        servers_window = tk.Toplevel(self)
        servers_window.title("Servidores Conectados")
        servers_window.geometry("400x400")
        servers_window.configure(bg=self.colors["bg"])

        tk.Label(servers_window, text="Servidores Conectados", font=("Arial", 16, "bold"),
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=10)

        # Frame para contener la lista y la barra de desplazamiento
        list_frame = tk.Frame(servers_window, bg=self.colors["bg"])
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        server_linksbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                bg=self.colors["bg"], fg=self.colors["fg"], font=("Arial", 16))
        server_linksbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=server_linksbox.yview)

        # Añadir servidores a la lista
        for server in self.temp_server_links:
            server_linksbox.insert(tk.END, server)

        # Limpiar la lista temporal
        self.temp_server_links = []

    def _add_channel_users(self, channel, users):
        """Añade usuarios a la lista temporal de un canal."""
        if not hasattr(self, "temp_channel_users"):
            self.temp_channel_users = {}  # Diccionario para almacenar usuarios por canal
        if channel not in self.temp_channel_users:
            self.temp_channel_users[channel] = []
        self.temp_channel_users[channel].extend(users)

    def _show_channel_users(self, channel):
        """Muestra la lista de usuarios de un canal en una ventana emergente."""
        if not hasattr(self, "temp_channel_users") or channel not in self.temp_channel_users:
            messagebox.showinfo(f"Usuarios en {channel}", "No se encontraron usuarios.")
            return

        # Crear la ventana para mostrar los usuarios
        users_window = tk.Toplevel(self)
        users_window.title(f"Usuarios en {channel}")
        users_window.geometry("300x400")
        users_window.configure(bg=self.colors["bg"])

        tk.Label(users_window, text=f"Usuarios en {channel}", font=("Arial", 16, "bold"),
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=10)

        # Frame para contener la lista y la barra de desplazamiento
        list_frame = tk.Frame(users_window, bg=self.colors["bg"])
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        user_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                bg=self.colors["bg"], fg=self.colors["fg"], font=("Arial", 14))
        user_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=user_listbox.yview)

        # Añadir usuarios a la lista
        for user in self.temp_channel_users[channel]:
            user_listbox.insert(tk.END, user)

        # Limpiar la lista temporal del canal
        del self.temp_channel_users[channel]

    # def _show_user_info(self):
    #     """Muestra la información del usuario en un cuadro de diálogo."""
    #     if hasattr(self, "user_info"):
    #         messagebox.showinfo("Información del Usuario", self.user_info)
    #         del self.user_info  # Limpiar la información después de mostrarla
    #     else:
    #         messagebox.showinfo("Información del Usuario", "No se encontró información.")

    def _update_context_menu(self):
        """Actualiza la información en el menú contextual."""
        if hasattr(self, "context_menu"):
            for widget in self.context_menu.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text=self.context_menu_info)


# Prueba independiente de la vista principal
if __name__ == "__main__":
    app = MainView()
    app.mainloop()

