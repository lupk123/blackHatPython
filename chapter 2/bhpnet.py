import sys
import socket
import getopt
import threading
import subprocess

listen = False
command = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    print "BHP Net Tool"
    print
    print "Usae: bhpnet.py -t target_host -p port"
    print "-l listen"
    print "-e --execute=file_to_run"
    print "-c --command"
    print "-u --upload=destination"
    print
    print
    print "Examples: "
    print "bhpnet.py -t 192.18.2.233 -p 555 -l 1 -c 1"
    print "bhpnet.py -t 192.18.2.233 -p 555 -l 1 -u=c:\\target.exe"
    print "bhpnet.py -t 192.18.2.233 -p 555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.2.233 -p 135"

def server_loop():
    global target

    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_command(command):
    command = command.rstrip()

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    return output

def client_handler(client_socket):
    global upload_destination
    global execute
    global command

    if len(upload_destination):
        file_buff = ""
        while True:
            data = client_socket.recv(4096)

            len_data = len(data)
            # print len_data

            if len_data <= 1:
                break
            else:
                client_socket.send("go on")
                file_buff += data

        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buff)
            file_descriptor.close()

            client_socket.send("Successful saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)


    if len(execute):
        output = run_command(execute)
        client_socket.send(output)

    if command:
        while True:
            client_socket.send("<BHP:#>")

            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(4096)
                response = run_command(cmd_buffer)

                client_socket.send(response)

def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((target, port))

        if len(buffer):
            # print buffer
            client.send(buffer)

        recv_len = 1
        response = ""
        while True:

            print
            buffer = raw_input("")
            buffer += "\n"
            client.send(buffer)

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response = data

                if recv_len < 4096:
                    break

            print response
            if len(response) > 15:
                break
    except:
        print "[*] Exception! Exiting."
    finally:
        client.close()


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    opts = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:l:e:t:p:c:u:", ["help", "listen", "execute", "target"
                                                                 "port", "command", "upload"])
    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload = True
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"

    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()

        client_sender(buffer)

    if listen:
        server_loop()

main()