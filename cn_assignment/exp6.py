from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import OVSKernelAP
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from mn_wifi.cli import CLI
from time import sleep

def topology():
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', position='10,30,0')
    sta2 = net.addStation('sta2', position='20,30,0')
    sta3 = net.addStation('sta3', position='30,30,0')
    ap1 = net.addAccessPoint('ap1', ssid='ssid-ap1', mode='g', channel='1', position='15,50,0')
    ap2 = net.addAccessPoint('ap2', ssid='ssid-ap2', mode='g', channel='6', position='35,50,0')
    c1 = net.addController('c1')

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])
    ap2.start([c1])

    # Enable monitor mode on sta1
    sta1.cmd('iw dev %s interface add mon0 type monitor' % sta1.params['wlan'][0])
    sta1.cmd('ifconfig mon0 up')

    # Start packet capture
    sta1.cmd('tcpdump -i mon0 -w wifi-control-capture.pcap &')

    sleep(2)  # Wait for capture to initialize

    # Trigger active scanning to capture probe traffic
    sta1.cmd('iw dev %s scan' % sta1.params['wlan'][0])
    sta2.cmd('iw dev %s scan' % sta2.params['wlan'][0])
    sta3.cmd('iw dev %s scan' % sta3.params['wlan'][0])

    info("*** Starting mobility\n")
    net.startMobility(time=3)
    net.mobility(sta1, 'start', time=4, position='10,30,0')
    net.mobility(sta1, 'stop', time=20, position='40,30,0')
    net.mobility(sta2, 'start', time=4, position='20,30,0')
    net.mobility(sta2, 'stop', time=20, position='5,30,0')
    net.mobility(sta3, 'start', time=4, position='30,30,0')
    net.mobility(sta3, 'stop', time=20, position='15,30,0')
    net.stopMobility(time=21)

    sleep(2)  # Give time for remaining frames to be captured
    sta1.cmd('pkill tcpdump')  # Stop the capture

    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
