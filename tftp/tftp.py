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
        self.count = 0


    # Starts the TFTP service thread
    def start(self):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind((self.host_ip, self.tftp_port))
        print('TFTP - listening on {}:{}'.format(self.host_ip, self.tftp_port))
        print('TFTP - serving files at {}'.format(self.data_dir))
        while True:
            pkt, addr = sock.recvfrom(self.BUFFER_SIZE)
            [opcode] = unpack('!H', pkt[0:2])
            if opcode == TFTPServer.RRQ_OPCODE:
                thread = Thread(target=self.__serve_file, args=(pkt, addr))
                thread.start()
            else:
                print('TFTP - unrecognized opcode while serving request')
                sock.sendto(self.pack_error(20, b'Illegal operation\0'), addr)
        sock.close()


    def pack_error(self, errcode, errmsg):
        error_opcode = pack('!H', TFTPServer.ERROR_OPCODE)
        error_code = pack('!H', errcode)
        packet = error_opcode + error_code + errmsg
        return packet


    def __serve_file(self, pkt, addr):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.settimeout(5)
        sock.bind((self.host_ip, 0))
        sock.connect(addr)
        
        filename = pkt[2:].split(b'\0')[0].decode()
        req_file = self.open_from_zip(filename)
        
        do_transfer = True
        retry = 0
        block = 1

        data_opcode = pack('!H', TFTPServer.DATA_OPCODE)

        if not req_file:
            do_transfer = False
            sock.send(self.pack_error(17, b'File not found\0'))
        else:
            print('TFTP - TRANSFER\t{}\t{}:{}'.format(filename, addr[0], addr[1]))

        while do_transfer:
            req_file.seek(512 * (block - 1))
            data = req_file.read(512)

            if data:
                sock.send(data_opcode + pack('!H', block) + data)
            try:
                recv_pkt = sock.recv(512)
            except:
                if retry > 5:
                    print('TFTP - CANCEL\t{}\t{}:{}'.format(filename, addr[0], addr[1]))
                    break
                else:
                    retry = retry + 1
                    print('TFTP - TIMEOUT\t{}\t{}:{}'.format(filename, addr[0], addr[1]))
                    continue
            [opcode] = unpack('!H', recv_pkt[0:2])
            [rblock] = unpack('!H', recv_pkt[2:4])
            if opcode == TFTPServer.ACK_OPCODE:
                if len(data) < 512:
                    do_transfer = False
                elif rblock == block:
                    block = block + 1
                else:
                    print('TFTP - BAD BLOCK\t{}\t{}:{}'.format(filename, addr[0], addr[1]))
            else:
                sock.send(self.pack_error(20, b'Illegal operation\0'))
                do_transfer = False

        if req_file:
            req_file.close()
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
