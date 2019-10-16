"""
This script will power cycle the raspberry pi's, causing them to attempt to PXE boot
snmp relevent OID = 1.3.6.1.2.1.105.1.1.1.3.1.x
where x = the port number to modify
setting to 1 will turn ON the port, setting to 2 will turn OFF the port
"""
import time # for sleep
from pysnmp.hlapi import *  # PySNMP library


def power_cycle(switch_port, switch_ip, community):
    turn_off(switch_port, switch_ip, community)
    time.sleep(1)
    turn_on(switch_port, switch_ip, community)


def turn_off(switch_port, switch_ip, community):
    print("power_cycle - Setting switch port {} to OFF".format(switch_port))
    errorIndication, errorStatus, errorIndex, varBinds = next(
        setCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransswitch_portTarget((switch_ip, 161)),
            ContextData(),
            ObjectType(
                ObjectIdentity("1.3.6.1.2.1.105.1.1.1.3.1." + str(switch_port)), Integer(2)
            ),  # value of 2 turns the switch_port OFF
        )
    )
    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print("power_cycle - not found")
    else:
        print("power_cycle - Set switch port {} to OFF".format(switch_port))


def turn_on(switch_port, switch_ip, community):
    print("power_cycle - Setting switch switch port {} to ON".format(switch_port))
    errorIndication, errorStatus, errorIndex, varBinds = next(
        setCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransswitch_portTarget((switch_ip, 161)),
            ContextData(),
            ObjectType(
                ObjectIdentity("1.3.6.1.2.1.105.1.1.1.3.1." + str(switch_port)), Integer(1)
            ),  # value of 1 turns the switch_port ON
        )
    )
    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print("power_cycle - not found")
    else:
        print("power_cycle - Set switch port {} to ON".format(port))
