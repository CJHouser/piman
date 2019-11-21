from threading import Thread
from sys import argv
from dhcp import dhcp
from tcp import tcp
from tftp import tftp
from utility import power_cycle
from utility import findport
import os

# may be able to use netifaces here https://github.com/al45tair/netifaces
direc = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/')[:-1])
config_file = open('{}/config.txt'.format(direc), 'r')
data_dir    = config_file.readline().rstrip()
tftp_port   = int(config_file.readline())
tcp_port    = int(config_file.readline())
server_ip   = config_file.readline().rstrip()
net_inter   = config_file.readline().rstrip()
subnet_mask = config_file.readline().rstrip()
hosts_file  = config_file.readline().rstrip()
switch_ip   = config_file.readline().rstrip()
community   = config_file.readline().rstrip()
remshell_file = config_file.readline().rstrip()
ip_lease_time = int(config_file.readline().rstrip())
config_file.close()

def server():
    tftp_thread = Thread(
            target=tftp.do_tftpd,
            args=[data_dir, tftp_port, server_ip],
            name="tftpd")
    tftp_thread.start()

    dhcp_thread = Thread(
            target=dhcp.do_dhcp,
            args=[hosts_file, subnet_mask, server_ip, ip_lease_time, net_inter],
            name="dhcpd")
    dhcp_thread.start()

    tcp_thread = Thread(
            target=tcp.do_tcp,
            args=[data_dir, tcp_port, server_ip],
            name="tcp")
    tcp_thread.start()

    tftp_thread.join()
    dhcp_thread.join()
    tcp_thread.join()

# Restarts multiple Raspberry Pi. A Pi will only be power cycled if it has a
# complete entry in the hosts file and is powered on.
def restart(host_ips):
    ip_mac_map = {ip: None for ip in host_ips}
    with open('{}/{}'.format(direc, hosts_file), 'r') as fd:
        for line in fd:
            mac, ip = line.split(';')[:2]
            ip_mac_map[ip] = mac
    for ip in host_ips:
        mac = ip_mac_map[ip]
        if mac:
            switch_port = findport.find_port(mac, switch_ip, community)
            if switch_port:
                power_cycle.power_cycle(switch_port, switch_ip, community)

def remshell(pi_address, port_on_localhost):
    mac = None
    print("remshell")
    with open('{}/{}'.format(direc, mac_ip_file), 'r') as fd:
        for line in fd:
            if pi_address == line.split(';')[1]:
                mac = line.split(';')[0]
                break;
        if mac:
            switch_port = findport.find_port(mac, switch_ip, community)
            if switch_port:
                with open('{}/remshell.txt'.format(direc), 'w') as f:
                    f.write(str(pi_address))
                    f.write(',')
                    f.write(str(port_on_localhost))
                power_cycle.power_cycle(switch_port, switch_ip, community)
            else:
                print('Switch port not found')
        else:
            print('{} not found'.format(pi_address))

def reinstall(host_ip):
    mac = None
    with open('{}/{}'.format(direc, hosts_file), 'r') as fd:
        for line in fd:
            if host_ip == line.split(';')[1]:
                mac = line.split(';')[0]
                break
    if mac:
        switch_port = findport.find_port(mac, switch_ip, community)
        if switch_port:
            with open('{}/reinstall.txt'.format(direc), 'w') as f:
                f.write(ip)
            power_cycle.power_cycle(switch_port, switch_ip, community)
        else:
            print('Switch port not found')
    else:
        print('{} not found'.format(ip))

def powercycle(switch_ports):
    for switch_port in switch_ports:
        power_cycle.power_cycle(switch_port, switch_ip, community)
