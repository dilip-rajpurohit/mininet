from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time
import matplotlib.pyplot as plt

def run_bandwidth_sharing_test(num_stations=3):
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    stations = []
    for i in range(1, num_stations + 1):
        sta = net.addStation(f'sta{i}', position=f'{10 + i*5},30,0')
        stations.append(sta)

    ap1 = net.addAccessPoint('ap1', ssid='bw-share', mode='g', channel='1', position='40,30,0')
    c0 = net.addController('c0')

    net.configureWifiNodes()
    net.plotGraph(max_x=100, max_y=60)
    net.build()
    c0.start()
    ap1.start([c0])

    time.sleep(1)

    info("*** Starting UDP server on AP\n")
    ap1.cmd('iperf -s -u -i 1 > /tmp/ap_udp_server.txt &')
    time.sleep(1)

    info("*** Running iperf clients on all stations\n")
    results = []
    for sta in stations:
        result = sta.cmd(f'iperf -c {ap1.IP()} -u -t 10 -i 1')
        results.append(result)

    net.stop()

    def parse_throughput(output):
        for line in reversed(output.splitlines()):
            if 'Mbits/sec' in line:
                return float(line.split()[-2])
        return 0.0

    throughputs = [parse_throughput(output) for output in results]
    return throughputs

def main():
    setLogLevel('info')
    num_stations = 4
    throughputs = run_bandwidth_sharing_test(num_stations)

    print("\n=== Bandwidth Sharing Results ===")
    for i, tp in enumerate(throughputs, 1):
        print(f"sta{i}: {tp:.2f} Mbps")

    # Plotting
    labels = [f'sta{i+1}' for i in range(len(throughputs))]
    plt.figure(figsize=(8, 6))
    plt.bar(labels, throughputs, color='skyblue')
    plt.ylabel('Throughput (Mbps)')
    plt.title('Bandwidth Sharing Between Stations (UDP)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('bandwidth_sharing_plot.png')
    plt.show()

if __name__ == '__main__':
    main()