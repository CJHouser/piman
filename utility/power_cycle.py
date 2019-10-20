# This script will power cycle the raspberry pi's, causing them to attempt to PXE boot
# SNMP relevent OID = 1.3.6.1.2.1.105.1.1.1.3.1.x
# where x = the switch port number to modify
# setting to 1 will turn ON the port, setting to 2 will turn OFF the port


import time # for sleep
from pysnmp.hlapi import *  # PySNMP library


# Turn power-over-ethernet at a switch port off and back on
# switch_port   :   switch port number to power cycle
# switch_ip     :   IP address of the switch
# community     :   SNMP community string
def power_cycle(switch_port, switch_ip, community):
    turn_off(switch_port, switch_ip, community)
    time.sleep(1)
    turn_on(switch_port, switch_ip, community)


# Turn power-over-ethernet at a switch port off
# switch_port   :   switch port number to power cycle
# switch_ip     :   IP address of the switch
# community     :   SNMP community string
def turn_off(switch_port, switch_ip, community):
    print("power_cycle - Setting switch port {} to OFF".format(switch_port))
    errorIndication, errorStatus, errorIndex, varBinds = next(
        setCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((switch_ip, 161)),
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


# Turn power-over-ethernet at a switch port on
# switch_port   :   switch port number to power cycle
# switch_ip     :   IP address of the switch
# community     :   SNMP community string
def turn_on(switch_port, switch_ip, community):
    print("power_cycle - Setting switch switch port {} to ON".format(switch_port))
    errorIndication, errorStatus, errorIndex, varBinds = next(
        setCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((switch_ip, 161)),
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
        print("power_cycle - Set switch port {} to ON".format(switch_port))
