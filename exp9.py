#!/usr/bin/env python

'Experiment 9: RSSI-based Handover with Hysteresis and Dwell Time'

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
    net = Mininet_wifi(controller=Controller, accessPoint=OVSKernelAP,
                       link=wmediumd, wmediumd_mode=interference)

    log_file = open("exp9_handover_log.txt", "w")

    def log(msg):
        print(msg)
        log_file.write(msg + "\n")

    info("*** Creating nodes\n")
    ap1 = net.addAccessPoint('ap1', ssid='ssid1', mode='g', channel='1',
                             position='40,50,0', range=45)
    ap2 = net.addAccessPoint('ap2', ssid='ssid2', mode='g', channel='6',
                             position='100,50,0', range=45)

    sta1 = net.addStation('sta1', ip='10.0.0.1/24', position='10,50,0', range=35)
    sta2 = net.addStation('sta2', ip='10.0.0.2/24', position='20,50,0', range=35)

    c0 = net.addController('c0')

    info("*** Configuring propagation model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring WiFi nodes\n")
    net.associationControl = 'ssf'
    net.configureWifiNodes()

    if '-p' not in args:
        net.plotGraph(max_x=130, max_y=100)

    info("*** Starting mobility\n")
    net.startMobility(time=0)
    net.mobility(sta1, 'start', time=1, position='10,50,0')
    net.mobility(sta1, 'stop', time=60, position='120,50,0')
    net.mobility(sta2, 'start', time=1, position='20,50,0')
    net.mobility(sta2, 'stop', time=60, position='120,50,0')
    net.stopMobility(time=61)

    info("*** Building and starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])

    log("\n*** Running AP association + RSSI logging ***")

    ap1_mac = ap1.cmd("cat /sys/class/net/ap1-wlan1/address").strip()
    ap2_mac = ap2.cmd("cat /sys/class/net/ap2-wlan1/address").strip()

    threshold = -75  # dBm
    hysteresis_margin = 5  # dBm
    dwell_time_sec = 10

    last_ap = {'sta1': None, 'sta2': None}
    handover_count = {'sta1': 0, 'sta2': 0}
    last_handover_time = {'sta1': -dwell_time_sec, 'sta2': -dwell_time_sec}

    sta1.cmd('iw dev sta1-wlan0 connect ssid1')
    sta2.cmd('iw dev sta2-wlan0 connect ssid1')

    for t in range(5, 145, 5):
        log(f"\n=== Status at simulated time ~{t}s ===")
        for sta in [sta1, sta2]:
            iw_output = sta.cmd(f"iw dev {sta.name}-wlan0 link")
            ap_match = re.search(r'Connected to ([0-9a-f:]{17})', iw_output)
            rssi_match = re.search(r'signal: (-\d+) dBm', iw_output)

            current_ap = ap_match.group(1) if ap_match else None
            rssi = int(rssi_match.group(1)) if rssi_match else None

            log(f"{sta.name} connected to: {current_ap or 'None'} | Signal: {rssi if rssi else 'None'} dBm")

            if current_ap and rssi is not None:
                time_since_last = t - last_handover_time[sta.name]
                if rssi < threshold and time_since_last >= dwell_time_sec:
                    log(f"Handover triggered for {sta.name} due to low RSSI ({rssi} dBm)")

                    if current_ap == ap1_mac and (last_ap[sta.name] != ap2_mac or rssi < threshold - hysteresis_margin):
                        sta.cmd('iw dev %s-wlan0 disconnect' % sta.name)
                        sta.cmd('iw dev %s-wlan0 connect ssid2' % sta.name)
                        last_ap[sta.name] = ap2_mac
                        last_handover_time[sta.name] = t
                        handover_count[sta.name] += 1

                    elif current_ap == ap2_mac and (last_ap[sta.name] != ap1_mac or rssi < threshold - hysteresis_margin):
                        sta.cmd('iw dev %s-wlan0 disconnect' % sta.name)
                        sta.cmd('iw dev %s-wlan0 connect ssid1' % sta.name)
                        last_ap[sta.name] = ap1_mac
                        last_handover_time[sta.name] = t
                        handover_count[sta.name] += 1

                else:
                    last_ap[sta.name] = current_ap

        time.sleep(2)

    log("\n*** Handover Summary ***")
    for sta in [sta1, sta2]:
        log(f"{sta.name} switched APs {handover_count[sta.name]} times.")

    log("\n*** You can run manual tests from the CLI ***")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()
    log_file.close()

if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)
