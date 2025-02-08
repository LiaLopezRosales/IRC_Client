import subprocess

# Path to the server executable
server_executable_path = 'tests/irc/dist/server'

# Run the server executable in the background
server_process = subprocess.Popen([server_executable_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("Server executed successfully")