from threading import Thread
from socket import AF_INET, SOCK_STREAM, socket
from struct import unpack, pack
from zipfile import ZipFile
import traceback
import os


# messages recieved from a Raspberry Pi
RECV_IS_INSTALLED = "IS_INSTALLED\n"
RECV_IS_UNINSTALLED = "IS_UNINSTALLED\n"
RECV_IS_FORMATTED =  "IS_FORMATTED\n"


# messages sent to a Raspberry Pi
SEND_BOOT = b"boot\n" + b"EOM\n"
SEND_FORMAT = b"format\n" + b"EOM\n"


direc = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/')[:-2])

class TCPServer:
    # TCPServer creates two TCP sockets, control and file socket.
    # The control socket serves control commands, such as INSTALLED, NEED FILE
    # The file socket transfers root file to the Raspberry Pi
    def __init__(self, data_dir, tcp_port, host_ip):
        self.data_dir = data_dir
        self.tcp_port = tcp_port
        self.host_ip = host_ip
        self.threads = []


    # Create separate threads for control and file service
    def start(self):
        try:
            self.tcp_socket = socket(AF_INET, SOCK_STREAM)
            self.tcp_socket.bind((self.host_ip, self.tcp_port))
            self.tcp_socket.listen()

            self.tcp_file_socket = socket(AF_INET, SOCK_STREAM)
            self.tcp_file_socket.bind((self.host_ip, 4444))
            self.tcp_file_socket.listen()

            tcp_thread = Thread(target=self.tcp_server_start, name="tcp_thread")
            self.threads.append(tcp_thread)
            tcp_thread.start()

            tcp_file_thread = Thread(target=self.tcp_file_start, name="tcp_file_thread")
            self.threads.append(tcp_file_thread)
            tcp_file_thread.start()
        except KeyboardInterrupt:
            self.tcp_socket.close()
            self.tcp_file_socket.close()


    # Serve the control socket
    def tcp_server_start(self):
        try:
            while True:
                (client_socket, client_addr) = self.tcp_socket.accept()
                tcp_thread = Thread(target=self.__process_requests,
                        args=[client_socket, client_addr],
                        name="tcp_client_thread")
                self.threads.append(tcp_thread)
                tcp_thread.start()
        except KeyboardInterrupt:
            self.tcp_socket.close()


    # Serve the file socket
    def tcp_file_start(self):
        try:
            while True:
                (client_socket, client_addr) = self.tcp_file_socket.accept()
                tcp_file_thread = Thread(target=self.__transfer_file,
                        args=[client_socket],
                        name="tcp_client_file_thread")
                self.threads.append(tcp_file_thread)
                tcp_file_thread.start()
        except KeyboardInterrupt:
            self.tcp_file_socket.close()


    # Serves incoming control requests
    def __process_requests(self, client_socket, client_addr):
        try:
            print("TCP  - serving client from: {}".format(client_addr))
            sockfd = client_socket.makefile()
            req = sockfd.readline()
            while req:
                print('TCP  - recieved request {}'.format(req), end = '')
                if req == RECV_IS_UNINSTALLED:
                    print("TCP  - uninstalled, sending format")
                    client_socket.send(SEND_FORMAT)
                elif req == RECV_IS_INSTALLED:
                    with open('{}/reinstall.txt'.format(direc), 'r+') as fd:
                        reinstall_list = [line.rstrip('\n') for line in fd]
                        fd.truncate(0)
                    if client_addr[0] in reinstall_list:
                        print("TCP  - reinstall required, sending format")
                        client_socket.send(SEND_FORMAT)
                    else:
                        print("TCP  - installed, sending boot signal")
                        client_socket.send(SEND_BOOT)        
                elif req == RECV_IS_FORMATTED:
                    print("TCP  - is formatted, sending file")
                    break
                #else:
                #    print("TCP  - unsupported request")
                req = sockfd.readline()
        except:
            traceback.print_exc()
        client_socket.close()


    # Serves boot file
    def __transfer_file(self, client_socket):
        print('TCP  - file transfer socket opened')
        zipfile = os.path.dirname(os.path.dirname(__file__))
        try:
            data = None
            try:
                with ZipFile(zipfile) as z:
                    print('TCP  - reading {}/rootfs.tgz'.format(self.data_dir))
                    fd = z.open('{}/rootfs.tgz'.format(self.data_dir))
                    data = fd.read()
            except:
                traceback.print_exc()

            if data:
                print('TCP  - sending rootfs.tgz')
                client_socket.send(data)
                print('TCP  - finished sending rootfs.tgz')
        except:
            traceback.print_exc()

        client_socket.close()
        print('TCP  - file transfer socket closed')


    def join(self):
        for thread in self.threads:
            thread.join()


# Simple TCP server that listens and serves data. For security reasons, only
#   read requests are supported.
# data_dir  :   path to boot files
# tcp_port  :   port that TCP service listens on
# host_ip   :   IP address of the machine hosting piman
def do_tcp(data_dir, tcp_port, host_ip):
    print('TCP  - starting')
    srvr = TCPServer(data_dir, tcp_port, host_ip)
    srvr.start()
    srvr.join()
