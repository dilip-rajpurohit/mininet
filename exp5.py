#!/usr/bin/env python

'802.11 Wireless LAN Emulation with Handoff'

import sys
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.node import Controller
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from mn_wifi.associationControl import AssociationControl

def topology(args):
    "Create a network with handoff demonstration."
    net = Mininet_wifi(controller=Controller, accessPoint=OVSKernelAP,
                       link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    # Stations with initial positions
    sta1 = net.addStation('sta1', position='25,50,0', range=25)  # starts near ap1
    sta2 = net.addStation('sta2', position='95,30,0', range=25)  # starts near ap2

    # Access Points with limited range
    ap1 = net.addAccessPoint('ap1', ssid='ssid-ap1', mode='g', channel='1',
                             position='30,40,0', range=25)
    ap2 = net.addAccessPoint('ap2', ssid='ssid-ap2', mode='g', channel='6',
                             position='90,40,0', range=25)

    # Controller
    c0 = net.addController('c0')

    info("*** Configuring propagation model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring WiFi nodes\n")
    net.configureWifiNodes()

    # Start plotting the graph if '-p' is not in the arguments
    if '-p' not in args:
        net.plotGraph(max_x=100, max_y=100)

    info("*** Starting mobility\n")
    net.startMobility(time=0)

    # Move sta1 from ap1 to ap2, and sta2 from ap2 to ap1
    net.mobility(sta1, 'start', time=1, position='25,50,0')
    net.mobility(sta1, 'stop', time=20, position='95,50,0')

    net.mobility(sta2, 'start', time=1, position='95,30,0')
    net.mobility(sta2, 'stop', time=20, position='25,30,0')

    net.stopMobility(time=21)

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)
