import subprocess, sys

def make_test(args, expeteted_output, error_msg):
    command = f"./run.sh {args}"

    info = subprocess.run([x for x in command.split(' ')], capture_output=True, text=True)
    output = info.stdout
    err = info.stderr

    if len(output) > 0:
        print(f"Execution output: {output}")

    if len(err) > 0:
        print(f"An error ocurred during execution: {err}")
    

    if not all([x in output for x in expeteted_output]):
        print("\033[31m" + f"Test: {command} failed with error {error_msg}")
        return False
    
    print("\033[32m" + f"Test: {command} completed")

    return True


# initial folder structure
# /: 1. directory 2. 2.txt
# /directory: 1.txt

tests = [
    ("-h 127.0.0.1 -p 21 -u user -w pass", ("220","230",), "Login Failed"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c PWD", ("257",), "/ directory listing failed"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c CWD -a /directory", ("250",), "change directory failed"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c QUIT", ("221",), "exiting ftp server failed"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c RETR -a 2.txt" , ("150","226",), "could not retrieve 2.txt file"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c STOR -a tests/ftp/new.txt -b new.txt", ("150", "226",), "file new.txt upload failed"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c RNFR -a 2.txt -b 3.txt", ("350", "250",), "rename from 2.txt to 3.txt failed"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c DELE -a new.txt", ("250",), "delete new.txt failed"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c MKD -a directory2", ("257",), "directory directory2 creation failed"),
    ("-h 127.0.0.1 -p 21 -u user -w pass -c RMD -a directory2", ("250",), "directory directory2 removal failed"),
]

succeed = True

for x in tests:
    succeed = make_test(x[0],x[1],x[2]) and succeed

if not succeed:
    print("Errors ocurred during tests process")
    sys.exit(1)

print("All commands executed successfully")