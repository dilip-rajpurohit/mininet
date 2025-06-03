#!/usr/bin/env python

from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time
import os
import re

def topology():
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)
    
    log_file = open("exp10_log.txt", "w")

    def log(msg):
        print(msg)
        log_file.write(msg + "\n")

    info("*** Creating nodes\n")
    sta = []
    for i in range(1, 6):  # Create 5 stations
        sta.append(net.addStation(f'sta{i}', position=f'{10*i},50,0'))

    ap1 = net.addAccessPoint('ap1', ssid='ssid-ap1', mode='g', channel='1', position='50,50,0')
    h1 = net.addHost('h1', ip='10.0.0.100')  # Web server
    c1 = net.addController('c1')

    info("*** Configuring propagation model\n")
    net.setPropagationModel(model="logDistance", exp=4)

    info("*** Configuring WiFi nodes\n")
    net.configureWifiNodes()

    info("*** Setting mobility model\n")
    net.setMobilityModel(time=0, model='RandomWalk', max_x=100, max_y=100, seed=42)

    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])

    info("*** Starting simple web server on h1\n")
    h1.cmd('python3 -m http.server 80 > /tmp/webserver.log 2>&1 &')
    time.sleep(2)

    info("*** Starting mobility\n")
    net.startMobility(time=0)

    log("\n*** Logging station associations, RSSI, and curl time ***")
    for sta_i in sta:
        sta_name = sta_i.name

        # Wait for association
        time.sleep(1)

        iw_output = sta_i.cmd(f"iw dev {sta_name}-wlan0 link")
        ap_match = re.search(r'Connected to ([0-9a-f:]{17})', iw_output)
        rssi_match = re.search(r'signal: (-\d+) dBm', iw_output)

        ap_mac = ap_match.group(1) if ap_match else "None"
        rssi = rssi_match.group(1) + " dBm" if rssi_match else "N/A"

        log(f"{sta_name} -> AP: {ap_mac}, RSSI: {rssi}")

        # Run curl test and capture curl time
        result = sta_i.cmd("/usr/bin/time -f 'curl_time: %e sec' curl -s http://10.0.0.100 2>&1")
        log(f"{sta_name} curl result:\n{result.strip()}\n")

    info("*** Waiting for curl tests to finish\n")
    time.sleep(5)

    info("*** Stopping mobility\n")
    net.stopMobility(time=40)

    info("*** Stopping network\n")
    net.stop()
    log_file.close()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
