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
        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        print('TFTP - connecting to {}:{}'.format(self.host_ip, self.tftp_port))
        self.server_socket.bind((self.host_ip, self.tftp_port))
        print('TFTP - serving files from {} on port {}'.format(self.data_dir, self.tftp_port))
        self.tftp_thread = Thread(target=self.__process_requests, name="tftpd")
        self.tftp_thread.start()


    # Serves data from piman.pyz
    def res_open(self, name):
        zipfile = os.path.dirname(os.path.dirname(__file__))
        fd = None
        try:
            with ZipFile(zipfile) as z:
                fd = z.open("{}/{}".format(self.data_dir, name))
        except KeyError:
            # The file was not found in the piman.pyz. It is a
            #   mystery what this returns, but it is assumed that it causes
            #   an error in the code that in turn causes a loop iteration
            #   to be skipped, which allows a new file to be requested.
            # This is a janky solution that is issue prone.
            #   It is functional, but the logic should be changed to
            #   handle this case properly.
            # A possible fix would be to allow None to be returned, then check
            #   for None whenever running this function.
            return open('', 'rb')
        return fd


    # Send files to a Raspberry Pi using an ephemeral port
    def send_file(self, address, file_path):
        # Create new socket
        sending_socket = socket(AF_INET, SOCK_DGRAM)
        # Pick a random open port to use for sending data
        sending_socket.bind(('', 0))
        print("connecting to {}:{}".format(self.host_ip, sending_socket.getsockname()[1]))
        # Open file to read data from
        transfer_file = self.res_open(file_path.decode())
        data = transfer_file.read()
        try:
            # Send entire stream of data on socket
            sending_socket.sendto(data, address)
        except:
            # So that we can close the connection in case something
            # happens to the client
            pass
        # Close socket connection when done
        sending_socket.close()

    
    # Handle valid and invalid requests and transfer data
    def __process_requests(self):
        print("TFTP - waiting for request")
        addr_dict = dict()
        # this while loop keeps our server running also accounting for ensuring the initial
        # data packet is retrieved by the host
        while True:
            pkt, addr = self.server_socket.recvfrom(self.BUFFER_SIZE)
            # the first two bytes of all TFTP packets is the opcode, so we can
            # extract that here. need network-byte order hence the '!'.
            [opcode] = unpack("!H", pkt[0:2])
            if opcode == TFTPServer.RRQ_OPCODE:
                # RRQ is a series of strings, the first two being the filename
                # and mode but there may also be options. see RFC 2347.
                #
                # we skip the first 2 bytes (the opcode) and split on b'\0'
                # since the strings are null terminated.
                #
                # because b'\0' is at the end of all strings split will always
                # give us an extra empty string at the end, so skip it with [:-1]
                strings_in_RRQ = pkt[2:].split(b"\0")[:-1]
                print("TFTP - got {} from {}".format(strings_in_RRQ, addr))
                addr_dict[addr] = [strings_in_RRQ[0], 0, 0]

                # data needed for our packet
                transfer_opcode = pack("!H", TFTPServer.DATA_OPCODE)

                try:
                    transfer_file = self.res_open(strings_in_RRQ[0].decode())
                    block_number = addr_dict[addr][1]
                    transfer_file.seek(512 * block_number)
                    data = transfer_file.read(512)
                    if data:
                        block_number +=1
                        addr_dict[addr][1] = block_number
                        transfer_block_number = pack("!H", block_number)
                        packet = transfer_opcode + transfer_block_number + data
                        self.server_socket.sendto(packet, addr)
                        
                except FileNotFoundError:
                    # send an error packet to the requesting host
                    error_opcode = pack("!H", TFTPServer.ERROR_OPCODE)
                    error_code = pack("!H", 17)
                    error_message = b"No such file within the directory\0"
                    packet = error_opcode + error_code + error_message    
            elif opcode == TFTPServer.ACK_OPCODE:
                # this loop begins to execute with the intention to send the rest of the data
                # in the case that our file is of a size greater than 512 bytes
                #while True:
                # retrieve the ack information from the client
                if addr in addr_dict:
                    [acked_block] = unpack("!H", pkt[2:4])
                    if acked_block == addr_dict[addr][1]:
                        try:
                            # opens the specified file in a read only binary form
                            file_name = addr_dict[addr][0]
                            transfer_file = self.res_open(
                                file_name.decode()
                            )

                            # block_number will remain an integer for file seeking purposes
                            block_number = addr_dict[addr][1]

                            # navigate to the corresponding 512-byte window in the transfer file
                            transfer_file.seek(512 * block_number)

                            # read up to the appropriate 512 bytes of data
                            data = transfer_file.read(512)

                            if data:
                                block_number += 1
                                addr_dict[addr][1] = block_number

                                # the transfer block number is a binary string representation of the block number
                                transfer_block_number = pack("!H", block_number)

                                # construct a data packet
                                packet = transfer_opcode + transfer_block_number + data

                                # send the initial data packet
                                self.server_socket.sendto(packet, addr)
                        except FileNotFoundError:
                            # send an error packet to the requesting host
                            error_opcode = pack("!H", TFTPServer.ERROR_OPCODE)
                            error_code = pack("!H", 17)
                            error_message = b"No such file within the directory\0"
                            packet = error_opcode + error_code + error_message

                    elif addr_dict[addr][2] < 3:
                        try:
                            # opens the specified file in a read only binary form
                            transfer_file = self.res_open(
                                addr_dict[addr][0].decode()
                            )

                            # block_number will remain an integer for file seeking purposes
                            block_number = addr_dict[addr][1] - 1

                            # navigate to the corresponding 512-byte window in the transfer file
                            transfer_file.seek(512 * block_number)

                            # read up to the appropriate 512 bytes of data
                            data = transfer_file.read(512)

                            if data:
                                # the transfer block number is a binary string representation of the block number
                                transfer_block_number = pack("!H", block_number)

                                # construct a data packet
                                packet = transfer_opcode + transfer_block_number + data

                                # send the initial data packet
                                self.server_socket.sendto(packet, addr)
                        except FileNotFoundError:
                            # send an error packet to the requesting host
                            error_opcode = pack("!H", TFTPServer.ERROR_OPCODE)
                            error_code = pack("!H", 17)
                            error_message = b"No such file within the directory\0"
                            packet = error_opcode + error_code + error_message
                else:
                    # form an error packet and send it to the invalid TID
                    error_opcode = pack("!H", TFTPServer.ERROR_OPCODE)
                    error_code = pack("!H", 21)
                    error_message = b"incorrect TID\0"
                    packet = error_opcode + error_code + error_message
                    self.server_socket.sendto(packet, addr)
            else:
                # form an error packet and send it to the invalid TID
                error_opcode = pack("!H", TFTPServer.ERROR_OPCODE)
                error_code = pack("!H", 20)
                error_message = b"illegal operation specified\0"
                packet = error_opcode + error_code + error_message
                self.server_socket.sendto(packet, addr)

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
