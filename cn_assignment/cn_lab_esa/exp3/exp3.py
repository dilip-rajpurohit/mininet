from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time
import matplotlib.pyplot as plt

def run_simulation():
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', position='10,30,0')   # Near the AP
    sta2 = net.addStation('sta2', position='100,30,0')  # Far from the AP
    ap1 = net.addAccessPoint('ap1', ssid='distance-test', mode='g', channel='1', position='50,30,0')
    c0 = net.addController('c0')

    net.configureWifiNodes()
    net.plotGraph(max_x=120, max_y=60)
    net.build()
    c0.start()
    ap1.start([c0])

    time.sleep(1)

    info("*** Running iperf tests\n")
    ap1.cmd('iperf -s -u -i 1 > /tmp/ap1_server.txt &')

    time.sleep(1)

    result_sta1 = sta1.cmd(f'iperf -c {ap1.IP()} -u -t 10 -i 1')
    result_sta2 = sta2.cmd(f'iperf -c {ap1.IP()} -u -t 10 -i 1')

    net.stop()

    # Parse iperf throughput
    def parse_iperf(output):
        for line in output.splitlines()[::-1]:
            if 'Mbits/sec' in line:
                return float(line.split()[-2])
        return 0.0

    tp_sta1 = parse_iperf(result_sta1)
    tp_sta2 = parse_iperf(result_sta2)

    return tp_sta1, tp_sta2

def main():
    setLogLevel('info')
    tp_sta1, tp_sta2 = run_simulation()

    print("\n=== Throughput Results (Mbps) ===")
    print(f"sta1 (near AP): {tp_sta1:.2f} Mbps")
    print(f"sta2 (far  AP): {tp_sta2:.2f} Mbps")

    # Plot
    labels = ['sta1 (near)', 'sta2 (far)']
    throughputs = [tp_sta1, tp_sta2]

    plt.figure(figsize=(6, 5))
    plt.bar(labels, throughputs, color=['green', 'red'])
    plt.ylabel('Throughput (Mbps)')
    plt.title('Throughput vs Distance from AP')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('distance_vs_throughput.png')
    plt.show()

if __name__ == '__main__':
    main()
