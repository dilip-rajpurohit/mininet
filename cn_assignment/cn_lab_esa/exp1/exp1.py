from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import matplotlib.pyplot as plt

def run():
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    # Positions chosen so stations have different path loss and thus different throughput
    sta1 = net.addStation('sta1', position='0,0,0', mode='a')    # farthest, lower throughput expected
    sta2 = net.addStation('sta2', position='25,25,0', mode='g')  # medium distance
    sta3 = net.addStation('sta3', position='40,40,0', mode='n')  # closest, highest throughput expected

    ap1 = net.addAccessPoint('ap1', ssid='macTest', mode='g', channel='1', position='20,40,0')
    c1 = net.addController('c1')

    net.setPropagationModel(model="logDistance", exp=4)

    info("*** Configuring WiFi nodes\n")
    net.configureWifiNodes()
    net.plotGraph(max_x=60, max_y=60)

    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])

    info("*** Waiting for stations to associate\n")
    net.waitConnected(timeout=5)

    info("*** Starting iperf server on ap1\n")
    ap1.cmd('iperf -s -u -i 1 > /dev/null &')

    results = {}

    # Bandwidth caps according to typical max PHY rates per protocol
    tests = {
        'sta1': ('6M', sta1),    # 802.11a max around 6 Mbps minimum rate
        'sta2': ('24M', sta2),   # 802.11g typical max around 24 Mbps
        'sta3': ('65M', sta3),   # 802.11n typical max around 65 Mbps (1 stream)
    }

    for name, (bw, sta) in tests.items():
        info(f"*** Testing throughput for {name} with bandwidth cap {bw}\n")
        output = sta.cmd(f'iperf -c {ap1.IP()} -u -b {bw} -t 10 -i 1')
        for line in output.split('\n'):
            if "sec" in line and "Mbits/sec" in line:
                parts = line.split()
                if len(parts) >= 8:
                    results[name] = float(parts[6])
                    break

    info("*** Stopping network\n")
    net.stop()

    info("*** Plotting results\n")
    labels = ['802.11a', '802.11g', '802.11n']
    throughput = [results.get('sta1', 0), results.get('sta2', 0), results.get('sta3', 0)]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, throughput, color=['blue', 'green', 'orange'])
    plt.ylabel('Throughput (Mbps)')
    plt.title('MAC Protocol Performance Comparison')
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.savefig("mac_protocol_comparison.png")
    info("*** Plot saved as mac_protocol_comparison.png\n")

if __name__ == '__main__':
    setLogLevel('info')
    run()
