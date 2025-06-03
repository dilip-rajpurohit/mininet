#!/usr/bin/env python

'802.11 Wireless LAN Emulation with Seamless Handover'

import sys
import time
import re
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import Controller
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference

def topology(args):
    "Network topology with 3 APs and 6 mobile stations demonstrating handover."
    net = Mininet_wifi(controller=Controller, accessPoint=OVSKernelAP,
                       link=wmediumd, wmediumd_mode=interference)

    log_file = open("exp7_handover_log.txt", "w")

    def log(msg):
        print(msg)
        log_file.write(msg + "\n")

    info("*** Creating nodes\n")
    # Access Points with overlapping coverage
    ap1 = net.addAccessPoint('ap1', ssid='ssid1', mode='g', channel='1',
                             position='40,50,0', range=35)
    ap2 = net.addAccessPoint('ap2', ssid='ssid2', mode='g', channel='6',
                             position='100,50,0', range=35)
    ap3 = net.addAccessPoint('ap3', ssid='ssid3', mode='g', channel='11',
                             position='160,50,0', range=35)

    c0 = net.addController('c0')

    stations = []
    for i in range(1, 7):
        sta = net.addStation(f'sta{i}', ip=f'10.0.0.{i}/24',
                             position=f'{20 + i * 5},30,0', range=20)
        stations.append(sta)

    info("*** Configuring propagation model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring WiFi nodes\n")
    net.associationControl = 'ssf'
    net.configureWifiNodes()

    if '-p' not in args:
        net.plotGraph(max_x=200, max_y=100)

    info("*** Starting mobility\n")
    net.startMobility(time=0)

    for idx, sta in enumerate(stations):
        start_time = 1 + idx
        stop_time = 25 + idx
        start_x = 20 + (idx * 5)
        net.mobility(sta, 'start', time=start_time, position=f'{start_x},30,0')
        net.mobility(sta, 'stop', time=stop_time, position='180,30,0')

    net.stopMobility(time=35)

    info("*** Building and starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    log("\n*** Running AP association + RSSI logging ***")
    last_ap = {sta.name: None for sta in stations}
    handover_count = {sta.name: 0 for sta in stations}

    for t in range(5,70, 5):
        log(f"\n=== Status at simulated time ~{t}s ===")
        for sta in stations:
            iw_output = sta.cmd(f"iw dev {sta.name}-wlan0 link")
            ap_match = re.search(r'Connected to ([0-9a-f:]{17})', iw_output)
            rssi_match = re.search(r'signal: (-\d+) dBm', iw_output)

            current_ap = ap_match.group(1) if ap_match else None
            signal = rssi_match.group(1) if rssi_match else "N/A"

            log(f"{sta.name} connected to: {current_ap} | Signal: {signal} dBm")

            if current_ap and last_ap[sta.name] and current_ap != last_ap[sta.name]:
                handover_count[sta.name] += 1
                log(f"Handover detected for {sta.name}!")

            if current_ap:
                last_ap[sta.name] = current_ap

        time.sleep(2)

    log("\n*** Handover Summary ***")
    for sta in stations:
        log(f"{sta.name} switched APs {handover_count[sta.name]} times.")

    log("\n*** You can run manual tests from the CLI ***")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()
    log_file.close()

if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)
