Carefree (Team 1) - CS158B - Fall 2019
---
# Development tips
There are a few potholes to watch out for that can cause problems while working on this code:

* __initram__
    
    In the directory install/initram there are some files which are used by the Raspberry Pis to remote boot. The Pi's receive these files via a zip file called initramfs.gz. Any time a change is made to the files in install/initram, a new initramfs.gz will need to be created. This can be done using the script install/initram/create_initramfs.gz.sh. The zip file will be placed in /install/boot by the script.

* __rootfs.tgz__
    
    TCP needs to send the Raspberry Pi's a file called rootfs.tgz. This file is NOT included in the repo and must be obtained from Ben Reed. It should be placed in install/boot with the rest of the boot data.

* __cmdline.txt__

    This file, located in install/boot, contains a hardcoded IP address that needs to be changed in order for remote boot to succeed. The IP address should be the IP address of the machine that is hosting piman.

# Configuration
* __hosts.csv__

    Each line in the hosts.csv file maps a Raspberry Pi's MAC address to an IP address. DHCP uses this file to assign Raspberry Pi's an IP address.
    
    `<Raspberry Pi MAC Address>;<IP address>;<Machine name>;<Timestamp>`

* __config.txt__

    Contains configuration information to allow piman to be run on any machine without making changes to the code. It MUST follow the following format:
    
```
    <Path to boot data>
    <TFTP port>
    <TCP port>
    <IP address of the machine hosting piman>
    <Subnet mask>
    <Path to hosts.csv>
    <IP address of the switch>
    <SNMP community phrase>
    <IP address lease time in seconds>
    <DNS Server IPv4 Address>
```

# Functionality

* Server
    
    `sudo python3 piman.pyz server`

* Restart
    
    `sudo python3 piman.pyz restart <IPv4 addresses>`

    `sudo python3 piman.pyz restart 172.30.1.11 172.30.1.14 172.30.1.20`

* Reinstall

    `sudo python3 piman.pyz reinstall <IPv4 address>`

    `sudo python3 piman.pyz reinstall 172.30.1.11'
    
### DHCP Server

The DHCP server utilized for this project is a very lightweight, barebone version of [this DHCP server](https://github.com/niccokunzmann/python_dhcp_server). To manually assign IPs to known MAC addresses, you can modify the `hosts.csv` file located in the root of the main directory. The Pis will send a DHCP packet to the manager which in then responds with an IP and the location of the TFTP server. 

### TFTP Server

The TFTP server is responsible for serving the boot files needed for each node to start-up correctly. The TFTP code is pretty straightforward, but here's somethings to look out for: 

* The TFTP server serves files from `install/boot` directory
* **You must put `rootfs.tgz` inside this directory**
* You can edit `hello_protocol.sh` located in `install/initram` directory. **Be sure to run `install/initram/create_initramfs.gz` to create the `initramfs.gz `**. Please note that `create_initramfs.gz` has been updated to place the created zip in the `install/boot` directory. 

### TCP Server

The server side of Hello Protocol is implemented here.

### Monitoring

#### Manager

There is a monitoring client running on the manager pi the periodically sends a get request to each node. The monitoring server running on the nodes respond with current status. To install the dependencies and run the client, run the following commands from the root directoyry of `pi-manager-ice`:

```sh
python3 -m pip install requests

# run server and redirect standard out to a log file
python3 monitoring/monitoring-client.py <path_to_config> > logs/status.log
```

#### Nodes
Each node pi (2-10) runs it's own custom made monitoring servers using Python 3 and Flask. The server currently supports one `GET` API endoint:

- [http://172.30.3.<pi_number>:3000/events](http://172.30.3.<pi_number>:3000/events) - This get request gives a response with the following information as JSON:

    | Key            | Value                      |
    |----------------|----------------------------|
    | time           | Current Timestamp          |
    | cpu_percent    | The CPU usage              |
    | memory_percent | The RAM usage              |
    | disk_percent   | The Disk usage             |
    | num_pids       | Number of active processes |


To get the server running, move over the `./monitoring` directory to each of the pi nodes and install the dependencies and run the server:

```sh
python3 -m pip install flask-restful
python3 -m pip install psutil
    
# run the server
python3 monitoring_server.py
```

#### Configuration and Alerts

To customize the timeout between each system check and/or the thresholds to alert, you can edit the `monitoring/monitoring.config`. 


Currently the system send a slack message to `#ice2` channel. You can create a slack app and set up webhooks to link your channel to the system. Follow [this](https://get.slack.help/hc/en-us/articles/115005265063-Incoming-WebHooks-for-Slack) slack tutorial.


### Start Up Scripts 

The `/etc/rc.local` file has been updated on the manager and the nodes to run the server and monitoring tools from startup. Take a look at it for each machine to get a better understanding of the startup process. 
