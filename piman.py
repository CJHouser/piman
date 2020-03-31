from threading import Thread
from sys import argv
from dhcp import dhcp
from tcp import tcp
from tftp import tftp
from utility import power_cycle
from utility import findport
import os
import yaml


# may be able to use netifaces here https://github.com/al45tair/netifaces
direc = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/')[:-1])
with open(direc + '/.piman.yaml', 'r') as fd:
    config = yaml.load(fd)
    community = config['SNMP-community']
    data_dir = config['boot-directory']
    dns_server = config['DNS-IPv4']
    hosts_file = config['hosts-file']
    ip_lease_time = config['DHCP-lease-time']
    net_inter = config['network-interface']
    server_ip = config['server-IPv4']
    subnet_mask = config['subnet-mask']
    switch_ip = config['switch-IPv4']
    tcp_port = config['tcp-port']
    tftp_port = config['tftp-port']


def server():
    tftp_thread = Thread(
            target=tftp.do_tftpd,
            args=[data_dir, tftp_port, server_ip],
            name="tftpd")
    tftp_thread.start()

    dhcp_thread = Thread(
            target=dhcp.do_dhcp,
            args=[hosts_file, subnet_mask, server_ip, ip_lease_time, net_inter, dns_server],
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


# rewrite for multiple reinstall
def reinstall(host_ip):
    host_ip = host_ip[0] # change later. func should take a list rather than string
    with open(direc + '/' + hosts_file, 'r') as fd:
        for line in fd:
            if host_ip == line.split(';')[1]:
                mac = line.split(';')[0]
                switch_port = findport.find_port(mac, switch_ip, community)
                if switch_port:
                    with open(direc + '/reinstall.txt', 'w') as f:
                        f.write(host_ip)
                    power_cycle.power_cycle(switch_port, switch_ip, community)
                else:
                    print('Switch port not found')


def powercycle(switch_ports):
    for switch_port in switch_ports:
        power_cycle.power_cycle(switch_port, switch_ip, community)


def remshell(pi_address, port_on_localhost):
    with open(direc + '/' + hosts_file, 'r') as fd:
        for line in fd:
            if pi_address == line.split(';')[1]:
                mac = line.split(';')[0]
                switch_port = findport.find_port(mac, switch_ip, community)
                if switch_port:
                    with open(direc + '/remshell.txt', 'w') as fd:
                        pi_addr = piaddress + ',' + str(port_on_localhost)
                        fd.write(pi_addr)
                    power_cycle.power_cycle(switch_port, switch_ip, community)
                else:
                    print('Switch port not found')
            else:
                print(pi_address + ' not found')
