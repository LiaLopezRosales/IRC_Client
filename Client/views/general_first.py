import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import textwrap
from client_network import ClientConnection
from Common.shared_constants import DEFAULT_HOST, DEFAULT_PORT

class MainView(tk.Tk):
    """
    Vista principal para el cliente IRC. Contiene:
    - Menú lateral desplegable.
    - Lista de canales/usuarios.
    - Área de chat.
    - Cinta de estado.
    """
    
    def __init__(self):
        super().__init__()
        self.title("Cliente IRC - UI Moderna")
        self.geometry("1000x700")
        self.configure(bg="#1E1E1E")  # Fondo oscuro
        
        # Conexión al servidor IRC
        self.connection = None

        # Variables de estado
        self.active_target = tk.StringVar(value="Ninguno seleccionado")
        self.active_target_type = -1
        self.connected = tk.StringVar(value="Desconectado")
        self.is_authenticated = False  # Usuario autenticado
        self.is_connected = False  # Estado de conexión al servidor
        self.username=None
        self.password=None
        self.nick=None

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


        # Agregar algunos elementos de ejemplo
        for channel in ["#general", "#python", "#random"]:
            self.channel_list.insert("end", channel)

        for user in ["Alice", "Bob", "Charlie"]:
            self.user_list.insert("end", user)

    def create_chat_area(self):
        """Área de chat principal con ajustes de tamaño y diseño."""
        self.chat_frame = tk.Frame(self, bg=self.colors["bg"], width=460)
        self.chat_frame.pack(side="right", fill="both", expand=True)
        self.chat_frame.pack_propagate(False)  # Desactiva el ajuste automático

        self.create_status_chat_bar()

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
            ("Cambiar Nick", self.change_nick_action),
            ("Conectar Servidor", self.connect_action),
            ("Info Servidor", self.server_info_action),
            ("Lista Servidores", self.server_list_action),
            ("Salir", self.quit)
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

    def create_status_chat_bar(self):
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


    def update_connection_status(self, connected=True):
        """Actualiza el estado de conexión."""
        if connected:
            self.connected.set("Conectado")
            self.status_bar.config(bg=self.colors["connect"])
        else:
            self.connected.set("Desconectado")
            self.status_bar.config(bg=self.colors["disconnect"])

    def change_nick_action(self):
        if self.is_authenticated:
            x = True
            while(x):
                new_user = simpledialog.askstring("Cambiar Usuario", "Ingresa tu nuevo nombre de usuario:")
                
                if new_user:
                    self.username_label.config(text=f"{new_user}")
                    messagebox.showinfo("Usuario Actualizado", f"Nuevo nombre de usuario: {new_user}")
                    x = False
                else:
                    messagebox.showerror("Error", "Debes completar el campos")
        else:
            messagebox.showerror("Error", "Debes autenticarte primero") 
        
    def server_info_action(self):
        messagebox.showinfo("Información", "Versión del servidor: IRC 2.0")

    def server_list_action(self):
        
        # esto se sustituirá con la lógica del IRC
        simulated_servers = [
            {"server_name": "local", "version": "v1.0"},
            {"server_name": "matcom", "version": "v3.4.1"},
            {"server_name": "teacher", "version": "v1.3.2"},
            {"server_name": "privet", "version": "v6.3"}
        ]

        # Crear una nueva ventana para mostrar los servidores
        servers_window = tk.Toplevel(self)
        servers_window.title(f"Servidores conectados")
        servers_window.geometry("400x400")
        servers_window.configure(bg=self.colors["bg"])

        tk.Label(servers_window, text=f"Servidores conectados", font=("Arial", 16, "bold"), bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=10)

        # Frame para contener la lista y la barra de desplazamiento
        list_frame = tk.Frame(servers_window, bg=self.colors["bg"])
        list_frame.pack(fill="both", expand=True)

        # Barra de desplazamiento
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        # Listbox para mostrar servidores y versiones
        user_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg=self.colors["bg"], fg=self.colors["fg"], font=("Arial", 16))
        user_listbox.pack(side="left", fill="both", expand=True)

        # Agregar los datos simulados al listbox
        for user in simulated_servers:
            user_listbox.insert(tk.END, f"{user['server_name']} - {user['version']}")

        scrollbar.config(command=user_listbox.yview)

    def send_message(self):
        """Envía un mensaje, muestra en el historial y limpia la entrada."""
        target = self.active_target
        message = self.message_entry.get()
        if message.strip():  # Evitar mensajes vacíos
            self.display_message(f"Tú: {message}", sender="self")
            self.message_entry.delete(0, tk.END)  # Limpieza automática
        else:
            messagebox.showwarning("Mensaje vacío", "No puedes enviar un mensaje vacío.")

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

    def connect_action(self):
        """Solicitar servidor y puerto en un solo formulario."""
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
                self.connection.connect_client(self.password,self.nick,self.username)
                self.is_connected = True
                self.update_connection_status(True)
                self.update_buttons()
                messagebox.showinfo("Conectado", f"Conectando a {server}:{port}...")
                connect_window.destroy()
            except ValueError:
                messagebox.showerror("Error", "El puerto debe ser un número.")

        connect_button = tk.Button(connect_window, text="Conectar", command=attempt_connection)
        connect_button.pack(pady=10)

    def disconnect_action(self):
        """Desconectarse y actualizar el estado."""
        if self.is_connected:
            self.is_connected = False
            self.update_connection_status(False)
            self.update_buttons()
            messagebox.showinfo("Desconectado", "Te has desconectado del servidor.")
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

    def open_context_menu(self):
        """Despliega un menú con opciones para canales o usuarios."""
        target = self.active_target.get()
        if target == "Ninguno seleccionado":
            messagebox.showerror("Error", "Debes seleccionar un canal o usuario primero.")
            return

        # Menú emergente
        context_menu = tk.Toplevel(self)
        context_menu.title(f"Opciones para {target}")
        context_menu.geometry("300x300")

        tk.Label(context_menu, text=f"Opciones para {target}").pack(pady=10)

        if self.active_target_type == 0:
            self.channel_topic = tk.Label(
                context_menu, 
                text=self.get_topic, 
                font=("Arial", 14, "bold")
            )
            self.channel_topic.pack(pady=5)
            tk.Button(context_menu, text="Cambiar Tema", font=("Arial", 13), command=self.change_topic).pack(pady=5)
            tk.Button(context_menu, text="Expulsar Usuario", font=("Arial", 13), command=self.kick_user).pack(pady=5)
            tk.Button(context_menu, text="Invitar al Canal", font=("Arial", 13), command=self.invite_to_channel).pack(pady=5)
            tk.Button(context_menu, text="Cambiar Modo", font=("Arial", 13), command=self.change_mode).pack(pady=5)
            tk.Button(context_menu, text="Mostrar Usuarios", font=("Arial", 13), command=self.check_users).pack(pady=5)
        else:
            tk.Label(context_menu, text=self.get_user_info, font=("Arial", 14, "bold")).pack(pady=5)
            tk.Button(context_menu, text="Cambiar Modo", font=("Arial", 13), command=self.change_mode).pack(pady=5)
            tk.Button(context_menu, text="Invita a un Canal", font=("Arial", 13), command=self.invite_user).pack(pady=5)

    def change_mode(self):
        target = self.active_target.get()
        mode = simpledialog.askstring("Establecer modo", "Ingresa el modo a establecer:")

    def change_topic(self):
        target = self.active_target.get()
        topic = simpledialog.askstring("Cambiar tema", "Ingresa el nuevo tema:")
        self.channel_topic.config(text=f"{topic}")

    def invite_to_channel(self):
        channel = self.active_target.get()
        target = simpledialog.askstring("Extender invitación", "Ingresa el nombre del usuario:")
        messagebox.showinfo("Notificación", f"Invitación enviada a {target}")

    def invite_user(self):
        target = self.active_target.get()
        channel = simpledialog.askstring("Extender invitación", "Ingresa el nombre del canal:")
        messagebox.showinfo("Notificación", f"Invitación enviada a {target}")

    def kick_user(self):
        target = self.active_target.get()
        kicked_user = simpledialog.askstring("Usuario a banear", "Ingresa el nombre del usuario:")

    def check_users(self):
        """Muestra una lista deslizante con los usuarios y permisos de un canal."""
        channel = self.active_target.get()

        # Simulación de datos recibidos tras un comando WHOIS
        # Estos datos deberían ser recuperados de la lógica real del cliente IRC
        simulated_users = [
            {"username": "Alice", "permissions": "+o (Operador)"},
            {"username": "Bob", "permissions": "+v (Voz)"},
            {"username": "Charlie", "permissions": "Sin permisos"},
            {"username": "Dana", "permissions": "+o (Operador)"}
        ]

        # Crear una nueva ventana para mostrar los usuarios
        users_window = tk.Toplevel(self)
        users_window.title(f"Usuarios en {channel}")
        users_window.geometry("300x400")
        users_window.configure(bg=self.colors["bg"])

        tk.Label(users_window, text=f"Usuarios en {channel}", font=("Arial", 16, "bold"), bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=10)

        # Frame para contener la lista y la barra de desplazamiento
        list_frame = tk.Frame(users_window, bg=self.colors["bg"])
        list_frame.pack(fill="both", expand=True)

        # Barra de desplazamiento
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        # Listbox para mostrar usuarios y permisos
        user_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg=self.colors["bg"], fg=self.colors["fg"], font=("Arial", 14))
        user_listbox.pack(side="left", fill="both", expand=True)

        # Agregar los datos simulados al listbox
        for user in simulated_users:
            user_listbox.insert(tk.END, f"{user['username']} - {user['permissions']}")

        scrollbar.config(command=user_listbox.yview)

    def get_topic(self):
        target = self.active_target.get()
        return "En espera"

    def get_user_info(self):
        user = self.active_target
        return " "

# Prueba independiente de la vista principal
if __name__ == "__main__":
    app = MainView()
    app.mainloop()


