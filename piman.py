# import click
from threading import Thread
from sys import argv


from dhcp import dhcp
from tcp import tcp
from tftp import tftp
from utility import power_cycle
from utility import findport


config_file = open('config.txt', 'r')
data_dir    = config_file.readline().rstrip()
tftp_port   = int(config_file.readline())
tcp_port    = int(config_file.readline())
host_ip     = config_file.readline().rstrip()
subnet_mask = config_file.readline().rstrip()
mac_ip_file = config_file.readline().rstrip()
switch_ip = config_file.readline().rstrip()
community   = config_file.readline().rstrip()
config_file.close()


def server(): 
    tftp_thread = Thread(target=tftp.do_tftpd, args=[data_dir, host_ip, tftp_port], name="tftpd")
    tftp_thread.start()

    dhcp_thread = Thread(target=dhcp.do_dhcp, args=[host_ip, subnet_mask, mac_ip_file], name="dhcpd")
    dhcp_thread.start()

    tcp_thread = Thread(target=tcp.do_tcp, args=[data_dir, tcp_port, host_ip], name="tcp")
    tcp_thread.start()

    tftp_thread.join()
    dhcp_thread.join()
    tcp_thread.join()


def restart(switch_port):
    power_cycle.power_cycle(switch_port, switch_ip, community)


def reinstall(ip):
    mac = None
    with open(mac_ip_file, 'r') as fd:
        for line in fd:
            if ip in line:
                mac = line.split(';')[0]
                break
    if mac:
        switch_port = findport.find_port(mac, switch_ip, community)
        if switch_port:
            with open('./reinstall.txt', 'w') as f:
                f.write(ip) 
            power_cycle.power_cycle(switch_port, switch_ip, community)
        else:
            print('Switch port not found')
    else:
        print('{} not found'.format(ip))
