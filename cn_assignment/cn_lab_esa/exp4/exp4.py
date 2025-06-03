from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import matplotlib.pyplot as plt
import time

def run_test(num_users):
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info(f"*** Creating {num_users} stations\n")
    stations = []
    for i in range(1, num_users + 1):
        sta = net.addStation(f'sta{i}', position=f'{10 + i*5},30,0')
        stations.append(sta)

    ap1 = net.addAccessPoint('ap1', ssid='mac-load-test', mode='g', channel='1', position='40,30,0')
    c0 = net.addController('c0')

    net.configureWifiNodes()
    net.plotGraph(max_x=100, max_y=100)
    net.build()
    c0.start()
    ap1.start([c0])

    info("*** Starting UDP servers on AP\n")
    ap1.cmd('iperf -s -u -i 1 > /tmp/ap_server.txt &')
    time.sleep(1)

    info("*** Running iperf clients\n")
    client_results = []
    for sta in stations:
        result = sta.cmd(f'iperf -c {ap1.IP()} -u -t 10 -i 1')
        client_results.append(result)

    net.stop()

    # Parse throughput results
    def parse_iperf(output):
        for line in output.splitlines()[::-1]:
            if 'Mbits/sec' in line:
                return float(line.split()[-2])
        return 0.0

    throughputs = [parse_iperf(res) for res in client_results]
    total_throughput = sum(throughputs)
    return throughputs, total_throughput

def main():
    setLogLevel('info')
    user_counts = [1, 2, 3, 4, 5]
    total_throughputs = []
    all_user_throughputs = {}

    for n in user_counts:
        info(f"\n=== Running test with {n} users ===\n")
        user_tps, total_tp = run_test(n)
        all_user_throughputs[n] = user_tps
        total_throughputs.append(total_tp)

    print("\n=== Summary ===")
    for n in user_counts:
        print(f"{n} users → Total Throughput: {total_throughputs[user_counts.index(n)]:.2f} Mbps")

    # Plot total throughput vs users
    plt.figure(figsize=(8, 6))
    plt.plot(user_counts, total_throughputs, marker='o', color='blue')
    plt.title('Load Impact on 802.11 MAC: Total Throughput vs Users')
    plt.xlabel('Number of Stations')
    plt.ylabel('Total Throughput (Mbps)')
    plt.grid(True)
    plt.savefig('mac_load_throughput.png')
    plt.show()

if __name__ == '__main__':
    main()