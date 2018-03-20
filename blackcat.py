#!/usr/bin/env python3.6
"""
blackcat.py

Practice creating a netcat-like application using Python 3. May expand on this periodically.
"""

__author__ = "Felajan"
__copyright__ = "Copyright 2018, Felajan"
__credits__ = ["Felajan", ]
__version__ = "1.0.0"
__maintainer__ = "Felajan"
__email__ = "felajan@protonmail.com"
__status__ = "Development"
__created_date__ = "2018-03-13"
__modified_date__ = "2018-03-20"

import argparse
import sys
import socket
import threading
import subprocess


class BlackCat():
    def __init__(self):
        usage = "connect to somewhere: %(prog)s  -t target_host -p port [options]\n" \
                "listen for inbound: %(prog)s -t 192.168.0.1 -p 5555 -l [options]"
        epilogue = "Examples: \n%(prog)s -t 192.168.0.1 -p 5555 -l -c\n" \
                   "%(prog)s -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe\n" \
                   "%(prog)s -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"\n" \
                   "echo 'ABCDEFGHI' | %(prog)s -t 192.168.0.1 -p 5555"
        parser = argparse.ArgumentParser(usage=usage, epilog=epilogue, allow_abbrev=False)
        parser.add_argument("-t", "--target_host", help="the target host")
        parser.add_argument("-p", "--port", type=int, help="the target host port")
        parser.add_argument("-l", "--listen", action='store_true',
                            help="listen on [host]:[port] for incoming connections")
        parser.add_argument("-e", "--execute=file_to_run", help="execute the given file upon receiving a connection")
        parser.add_argument("-c", "--command", action='store_true', default=None, help="initialize a command shell")
        parser.add_argument("-u", "--upload", default=None, help="upon receiving connection upload piped file "
                                                                 "and write to [upload destination]")

        if not len(sys.argv[1:]):
            parser.print_help()
            sys.exit(0)

        self.args = parser.parse_args()

        # are we going to listen or just send data from stdin
        if not self.args.listen and len(self.args.target_host) and self.args.port > 0:
            # read in the buffer from the commandline
            # this will block, so send CTRL-D if not sending input
            # to stdin
            buffer = sys.stdin.read()

            # send data off
            self.client_sender(buffer)

        # we are going to listen and potentially
        # upload things, execute commands, and drop a shell back
        # depending on our command line options above
        if self.args.listen:
            self.server_loop()

    def client_sender(self, buffer):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # connect to our target host
            client.connect((self.args.target_host, self.args.port))

            if len(buffer):
                client.send(buffer)

            while True:
                # now wait for data back
                recv_len = 1
                response = ""

                while recv_len:
                    data = client.recv(4096)
                    recv_len = len(data)
                    response += data

                    if recv_len < 4096:
                        break

                print(response)

                # wait for more input
                buffer = input("")
                buffer += "\n"

                # send it off
                client.send(buffer)

        except:
            print("[*] Exception! Exiting.")
            # tear down the connection
            client.close()

    def server_loop(self):
        # if no target is defined, we listen on all interfaces
        if not len(self.args.target_host):
            self.args.target_host = "0.0.0.0"

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.args.target_host, self.args.port))
        server.listen(5)

        while True:
            client_socket, addr = server.accept()

            # spin off a thread to handle our new client
            client_thread = threading.Thread(target=self.client_handler, args=(client_socket,))
            client_thread.start()

    @staticmethod
    def run_command(command):
        # trim in the newline
        command = command.rstrip()

        # run the command and get the output back
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        except:
            output = "Failed to execute comand.\r\n"

        # send the output back to the client
        return output

    def client_handler(self, client_socket):
        # check for upload
        if len(self.args.upload_destination):
            # read in all of the bytes and write to our destination
            file_buffer = ""

            # keep reading data until none is available
            while True:
                data = client_socket.recv(1024)

                if not data:
                    break
                else:
                    file_buffer += data

            # now we take these bytes and try to write them out
            try:
                file_descriptor = open(self.args.upload_destination, "wb")
                file_descriptor.write(file_buffer)
                file_descriptor.close()

                # acknowledge that we wrote the file out
                client_socket.send("Successfully saved to {}\r\n".format(self.upload_destination))
            except:
                client_socket.send("Failed to save file to {}\r\n".format(self.upload_destination))

        # check for command execution
        if len(execute):
            # run the command
            output = self.run_command(execute)

            client_socket.send(output)

        # now we go into another loop if a command shell was requested
        if self.command:
            while True:
                # show a simple prompt
                client_socket.send("<BlkCat:#> ")
                # now we receie until we see a linefeed (enter key)
                cmd_buffer = ""
                while "\n" not in cmd_buffer:
                    cmd_buffer += client_socket.recv(1024)
                # send back the command output
                response = self.run_command(cmd_buffer)
                # send back the response
                client_socket.send(response)


if __name__ == "__main__":
    BlackCat()
