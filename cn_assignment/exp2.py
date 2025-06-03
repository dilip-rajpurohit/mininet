#!/usr/bin/python

from mininet.node import Controller, OVSKernelSwitch
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Station, OVSKernelAP
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from subprocess import call


def myNetwork():

    net = Mininet_wifi(topo=None,
                       build=False,
                       link=wmediumd,
                       wmediumd_mode=interference,
                       ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0 = net.addController(name='c0',
                           controller=Controller,
                           protocol='tcp',
                           port=6653)

    info( '*** Add switches/APs\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    ap1 = net.addAccessPoint('ap1', cls=OVSKernelAP, ssid='ap1-ssid',
                             channel='1', mode='g', position='517.0,97.0,0')
    ap2 = net.addAccessPoint('ap2', cls=OVSKernelAP, ssid='ap2-ssid',
                             channel='1', mode='g', position='905.0,735.0,0')
    ap3 = net.addAccessPoint('ap3', cls=OVSKernelAP, ssid='ap3-ssid',
                             channel='1', mode='g', position='1576.0,136.0,0')
    ap4 = net.addAccessPoint('ap4', cls=OVSKernelAP, ssid='ap4-ssid',
                             channel='1', mode='g', position='1403.0,74.0,0')
    ap5 = net.addAccessPoint('ap5', cls=OVSKernelAP, ssid='ap5-ssid',
                             channel='1', mode='g', position='214.0,799.0,0')

    info( '*** Add hosts/stations\n')
    sta1 = net.addStation('sta1', ip='10.0.0.1',
                           position='306.0,49.0,0')
    sta2 = net.addStation('sta2', ip='10.0.0.2',
                           position='402.0,106.0,0')
    sta3 = net.addStation('sta3', ip='10.0.0.3',
                           position='292.0,147.0,0')
    sta4 = net.addStation('sta4', ip='10.0.0.4',
                           position='1777.0,136.0,0')
    sta5 = net.addStation('sta5', ip='10.0.0.5',
                           position='1776.0,224.0,0')
    sta6 = net.addStation('sta6', ip='10.0.0.6',
                           position='1697.0,294.0,0')
    sta7 = net.addStation('sta7', ip='10.0.0.7',
                           position='1218.0,66.0,0')
    sta8 = net.addStation('sta8', ip='10.0.0.8',
                           position='1095.0,693.0,0')
    sta9 = net.addStation('sta9', ip='10.0.0.9',
                           position='1126.0,789.0,0')
    sta10 = net.addStation('sta10', ip='10.0.0.10',
                           position='1021.0,799.0,0')
    sta11 = net.addStation('sta11', ip='10.0.0.11',
                           position='81.0,767.0,0')

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info( '*** Add links\n')
    net.addLink(ap5, ap1)
    net.addLink(ap4, ap3)
    net.addLink(ap1, s1)
    net.addLink(s1, s2)
    net.addLink(s2, ap2)
    net.addLink(s2, ap3)

    net.plotGraph(max_x=1000, max_y=1000)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches/APs\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('ap1').start([])
    net.get('ap2').start([])
    net.get('ap3').start([])
    net.get('ap4').start([])
    net.get('ap5').start([])

    info( '*** Post configure nodes\n')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

