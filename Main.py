import argparse
from Client.client_main import run_client
from Server.server_main import run_server

def main():
    parser = argparse.ArgumentParser(description="Sistema IRC con cliente y servidor.")
    parser.add_argument('--mode', choices=['client', 'server'], required=True,
                        help="Modo de ejecución: cliente o servidor")
    args = parser.parse_args()

    if args.mode == 'client':
        run_client()
    elif args.mode == 'server':
        run_server()

if __name__ == "__main__":
    main()
