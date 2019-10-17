#1. SSH into the bastion host 
#2. run `snmpwalk -v1 -c public@6 172.30.6.128 mib-2 | grep -i c6`
#
#3. run `snmpwalk -m BRIDGE-MIB -v1 -c public@6 172.30.6.128 mib-w | grep -i c6`
#    Noticed output `BRIDGE-MIB::dot1dTpFdbAddress.‘.M....’ = STRING: f0:4d:a2:8:c6:ca`
#
#4. googled 'dot1dTpFdbAddress' -> http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.3.6.1.2.1.17.4.3.1.1
#    found out that OID is 1.3.6.1.2.1.17.4.3.1
#
#5. run `snmpwalk  -v1 -c public@6 172.30.6.128  -Ci .1.3.6.1.2.1.17.4.3.1`
#    Notice output 
#      ```
#      SNMPv2-SMI::mib-2.17.4.3.1.1.184.39.235.231.174.106 = Hex-STRING: B8 27 EB E7 AE 6A
#      SNMPv2-SMI::mib-2.17.4.3.1.1.240.77.162.7.28.70 = Hex-STRING: F0 4D A2 07 1C 46
#      ```
#    led to http://oid-info.com/get/1.3.6.1.2.1.17.4.3.1
#    
#6. run `snmpwalk  -v1 -c public@6 172.30.6.128  -Ci .1.3.6.1.2.1.17.4.3.1`
#    Notice output
#      ```
#      SNMPv2-SMI::mib-2.17.4.3.1.1.240.77.162.8.198.202 = Hex-STRING: F0 4D A2 08 C6 CA
#       --- --- --- > SNMPv2-SMI::mib-2.17.4.3.1.2.240.77.162.8.198.202 = INTEGER: 24
#      SNMPv2-SMI::mib-2.17.4.3.1.3.240.77.162.8.198.202 = INTEGER: 3
#      ```


import click
import sys
from pysnmp.hlapi import *


@click.command()
@click.argument('mac_addr')
@click.argument('switch_ip')
@click.argument('community')
def find_port(mac_addr, switch_ip, community):
    """
    source: http://snmplabs.com/pysnmp/quick-start.html#fetch-snmp-variable
    """
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((switch_ip, 161)),
            ContextData(),
            ObjectType(
                ObjectIdentity(
                    "1.3.6.1.2.1.17.4.3.1.2.{}".format(mac_in_decimal(mac_addr))
                )
            ),
        )
    )

    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print(
            "%s at %s"
            % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1][0] or "?",
            )
        )
    else:
        result = varBinds[0].prettyPrint()
        print(result)
        return result.split(" = ")[1]


def mac_in_decimal(mac_addr):
    parts = []
    for part in mac_addr.split(":"):
        parts.append(str(int(part, 16)))
    return ".".join(parts)


if __name__ == '__main__':
    find_port()