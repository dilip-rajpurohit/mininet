from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time
import matplotlib.pyplot as plt

def setup_network():
    """Set up network with two Access Points and one mobile station."""
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    # Create the station and access points
    sta1 = net.addStation('sta1', position='10,30,0')  # Near AP1 initially
    ap1 = net.addAccessPoint('ap1', ssid='wifi-network', mode='g', channel='1', position='50,30,0')
    ap2 = net.addAccessPoint('ap2', ssid='wifi-network', mode='g', channel='1', position='150,30,0')
    c0 = net.addController('c0')

    # Configure the network
    net.configureWifiNodes()
    net.plotGraph(max_x=200, max_y=60)
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])

    return net, sta1, ap1, ap2

def start_iperf_test(sta1, ap, ap_ip):
    """Start the iperf test to measure throughput."""
    info("*** Starting iperf server on AP\n")
    ap.cmd('killall -9 iperf')  # Make sure no old iperf server is running
    ap.cmd('iperf -s -u -i 1 > /tmp/ap_server.txt &')
    time.sleep(1)

    info("*** Starting iperf client on sta1\n")
    result = sta1.cmd(f'iperf -c {ap_ip} -u -t 30 -i 1')
    return result

def move_station(sta1, new_position):
    """Move the station to a new position (simulate handover)."""
    info(f"Moving station to {new_position}\n")
    sta1.setPosition(new_position)
    time.sleep(5)  # Simulate time taken for handover

def parse_iperf_output(output):
    """Parse iperf output to extract throughput."""
    throughput = 0.0
    for line in output.splitlines():
        if 'Mbits/sec' in line and 'Server Report' not in line:
            parts = line.split()
            try:
                throughput = float(parts[-2])
            except (ValueError, IndexError):
                continue
    return throughput

def measure_handover_time():
    """Measure the time taken for the handover to complete."""
    net, sta1, ap1, ap2 = setup_network()

    # Initial test with AP1
    info("*** Running initial iperf test with AP1\n")
    ap1_ip = ap1.IP()
    initial_result = start_iperf_test(sta1, ap1, ap1_ip)

    # Move station to AP2
    disconnect_time = time.time()
    move_station(sta1, '150,30,0')
    reconnect_time = time.time()

    # Handover performance test with AP2
    info("*** Running iperf test after handover to AP2\n")
    ap2_ip = ap2.IP()
    handover_result = start_iperf_test(sta1, ap2, ap2_ip)

    # Measure handover time
    handover_time = reconnect_time - disconnect_time
    print(f"Handover Time: {handover_time:.2f} seconds")

    # Stop the network
    net.stop()

    # Parse results
    initial_throughput = parse_iperf_output(initial_result)
    handover_throughput = parse_iperf_output(handover_result)
    print(f"Initial Throughput (AP1): {initial_throughput} Mbps")
    print(f"Throughput after Handover (AP2): {handover_throughput} Mbps")

    # Plot results
    labels = ['Initial', 'Post Handover']
    throughput_data = [initial_throughput, handover_throughput]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, throughput_data, color='green')
    plt.ylabel('Throughput (Mbps)')
    plt.title(f'Handover Throughput Comparison\nHandover Time: {handover_time:.2f} seconds')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('handover_throughput.png')
    plt.show()

if __name__ == '__main__':
    setLogLevel('info')
    measure_handover_time()
