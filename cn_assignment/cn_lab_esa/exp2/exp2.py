from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time

def run_simulation(rts_cts='off'):
    info(f"\n=== Running with RTS/CTS: {rts_cts.upper()} ===\n")
    net  = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode =interference)

    # Place stations far apart so they can't hear each other
    sta1 = net.addStation('sta1', position='10,30,0')
    sta2 = net.addStation('sta2', position='80,30,0')
    ap1 = net.addAccessPoint('ap1', ssid='ht-ssid', mode='g', channel='1', position='45,30,0')
    c0 = net.addController('c0')

    net.configureWifiNodes()
    net.plotGraph(max_x=100, max_y=100)
    net.build()
    c0.start()
    ap1.start([c0])

    # Set RTS/CTS threshold
    sta1.cmd(f'iwconfig sta1-wlan0 rts {rts_cts}')
    sta2.cmd(f'iwconfig sta2-wlan0 rts {rts_cts}')
    ap1.cmd(f'iwconfig ap1-wlan1 rts {rts_cts}')

    time.sleep(1)

    # Start iperf servers on AP
    ap1.cmd('iperf -s -u -i 1 > /tmp/ap_server.txt &')

    time.sleep(1)

    info("*** Starting iperf clients\n")
    sta1_result = sta1.cmd(f'iperf -c {ap1.IP()} -u -t 10 -i 1')
    sta2_result = sta2.cmd(f'iperf -c {ap1.IP()} -u -t 10 -i 1')

    net.stop()

    # Parse throughput
    def parse_iperf(output):
        for line in output.splitlines()[::-1]:
            if 'Mbits/sec' in line:
                return float(line.split()[-2])
        return 0.0

    tp_sta1 = parse_iperf(sta1_result)
    tp_sta2 = parse_iperf(sta2_result)

    return tp_sta1, tp_sta2

def main():
    setLogLevel('info')
    tp_no_rts = run_simulation(rts_cts='off')
    tp_with_rts = run_simulation(rts_cts='2347')  # Enable RTS/CTS for all packets

    print("\n=== Throughput Summary ===")
    print("Without RTS/CTS:")
    print(f"  sta1: {tp_no_rts[0]:.2f} Mbps, sta2: {tp_no_rts[1]:.2f} Mbps")
    print("With RTS/CTS:")
    print(f"  sta1: {tp_with_rts[0]:.2f} Mbps, sta2: {tp_with_rts[1]:.2f} Mbps")

    # Optional: plot results
    try:
        import matplotlib.pyplot as plt

        labels = ['sta1', 'sta2']
        x = range(len(labels))
        width = 0.35

        plt.figure(figsize=(8, 6))
        plt.bar(x, tp_no_rts, width=width, label='Without RTS/CTS', color='red')
        plt.bar([i + width for i in x], tp_with_rts, width=width, label='With RTS/CTS', color='green')

        plt.xlabel('Stations')
        plt.ylabel('Throughput (Mbps)')
        plt.title('Hidden Terminal Problem: RTS/CTS Impact')
        plt.xticks([i + width/2 for i in x], labels)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('hidden_terminal_throughput_exp2.png')
        plt.show()
    except ImportError:
        print("matplotlib not installed, skipping plot.")

if __name__ == '__main__':
    main()