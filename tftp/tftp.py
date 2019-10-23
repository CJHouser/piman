from socket import AF_INET, SOCK_DGRAM, socket
from struct import unpack, pack
from threading import Thread
from zipfile import ZipFile
import os


# TFTP data packets consist of a 2-byte opcode, 2-byte block number, and up
#   to 512-byte data portion
# Although we could minimize since our server is solely getting RRQ and Ack
#   packets we could have set the buffer to a more optimized value (i.e.
#   filenames on Mac OSX can have up to 256 characters so we could limit
#   the buffer to the max size of a RRQ packet) but for better practice
#   it's been set to the max data packet length in TFTP
class TFTPServer:
    RRQ_OPCODE = 1
    DATA_OPCODE = 3
    ACK_OPCODE = 4
    ERROR_OPCODE = 5
    BUFFER_SIZE = 516
    
    
    # The TFTPServer class encapsulates the methods required for running a read
    #   only TFTP server
    # data_dir  :   path to boot files
    # tftp_port :   port that TFTP service listens on
    # host_ip   :   IP address of the machine hosting piman
    def __init__(self, data_dir, tftp_port, host_ip):
        self.data_dir = data_dir
        self.tftp_port = tftp_port
        self.host_ip = host_ip


    # Starts the TfTP service thread
    def start(self):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind((self.host_ip, self.tftp_port))
        print('TFTP - listening on {}:{}'.format(self.host_ip, self.tftp_port))
        print('TFTP - serving files at {}'.format(self.data_dir))
        while True:
            pkt, addr = sock.recvfrom(self.BUFFER_SIZE)
            [opcode] = unpack('!H', pkt[0:2])
            if opcode == TFTPServer.RRQ_OPCODE:
                thread = Thread(target=self.__serve_file, args=(pkt, addr), name='TFTP serve file')
                thread.start()
            else:
                print('TFTP - unrecognized opcode while serving request')
                print(pkt)
        sock.close()


    # Serves a single file on an ephemeral port
    def __serve_file(self, pkt, addr):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind((self.host_ip, 0))
        data_opcode = pack('!H', TFTPServer.DATA_OPCODE)
        filename = pkt[2:].split(b'\0')[0]
        requested_file = self.open_from_zip(filename.decode())
        if not requested_file:
            sock.close()
            return
        block = 1
        do_read = True
        print('TFTP - sending {} from {}:{} to {}'.format(
            filename, self.host_ip, sock.getsockname()[1], addr))
        while do_read:
            requested_file.seek(512 * (block - 1))
            data = requested_file.read(512)
            if data:
                data_pkt = data_opcode + pack('!H', block) + data
                sock.sendto(data_pkt, addr)
            else:
                do_read = False
            recv_pkt = sock.recv(self.BUFFER_SIZE) #need to check for timeout in case ack lost
            [opcode] = unpack('!H', recv_pkt[0:2])
            if opcode == TFTPServer.ACK_OPCODE:
                block = block + 1
            else:
                print('TFTP - unrecognized opcode while serving file')
                print(recv_pkt)
        print('TFTP - finished sending {}'.format(filename))
        requested_file.close()
        sock.close()


    # Serves data from piman.pyz
    def open_from_zip(self, filename):
        zipfile = os.path.dirname(os.path.dirname(__file__))
        fd = None
        with ZipFile(zipfile) as zf:
            filepath = '{}/{}'.format(self.data_dir, filename)
            if filepath in zf.namelist():
                fd = zf.open(filepath)
        return fd


    def join(self):
        self.tftp_thread.join()


# TFTP server that listens and serves a boot file from a specified path
# For security reasonse, only read requests are supported.
# data_dir  :   path to boot files
# tftp_port :   port that TFTP service listens on
# host_ip   :   IP address of the machine hosting piman
def do_tftpd(data_dir, tftp_port, host_ip):
    print("TFTP - starting")
    srvr = TFTPServer(data_dir, tftp_port, host_ip)
    srvr.start()
    srvr.join()
    print("TFTP - terminating")
