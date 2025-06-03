from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time
import matplotlib.pyplot as plt

def setup_network():
    """Setup the network with two APs and a mobile station."""
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    # Create stations
    sta1 = net.addStation('sta1', position='10,30,0')  # Initial position near AP1
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
    """Start the iperf test to measure throughput, packet loss, and delay."""
    info("*** Starting iperf server on AP\n")
    ap.cmd('killall -9 iperf')  # Kill any previous iperf processes
    ap.cmd('iperf -s -u -i 1 > /tmp/ap_server.txt &')
    time.sleep(1)

    info("*** Starting iperf client on sta1\n")
    result = sta1.cmd(f'iperf -c {ap_ip} -u -t 30 -i 1')
    return result

def move_station(sta1, new_position):
    """Move the station to the new position (simulating handover)."""
    info(f"Moving station to {new_position}\n")
    sta1.setPosition(new_position)
    time.sleep(5)  # Simulate the handover time

def parse_iperf_output(output):
    """Parse iperf output to extract throughput and packet loss."""
    throughput = 0.0
    packet_loss = 0.0
    for line in output.splitlines():
        if 'Mbits/sec' in line and 'Server Report' not in line:
            parts = line.split()
            try:
                throughput = float(parts[-2])
            except (ValueError, IndexError):
                continue
        if 'loss' in line:
            try:
                packet_loss = float(line.split()[6].strip('%'))
            except (ValueError, IndexError):
                continue
    return throughput, packet_loss

def main():
    setLogLevel('info')

    # Setup the network
    net, sta1, ap1, ap2 = setup_network()

    # Start initial iperf test with sta1 connected to AP1
    info("*** Running initial iperf test with AP1\n")
    ap1_ip = ap1.IP()
    initial_result = start_iperf_test(sta1, ap1, ap1_ip)

    # Parse the results before handover
    initial_throughput, initial_loss = parse_iperf_output(initial_result)
    print(f"Initial Throughput (AP1): {initial_throughput} Mbps")
    print(f"Initial Packet Loss (AP1): {initial_loss}%")

    # Move the station to AP2 (simulate handover)
    move_station(sta1, '150,30,0')  # Move sta1 near AP2

    # After handover, start iperf test with AP2
    info("*** Running iperf test after handover to AP2\n")
    ap2_ip = ap2.IP()
    handover_result = start_iperf_test(sta1, ap2, ap2_ip)

    # Parse the results after handover
    handover_throughput, handover_loss = parse_iperf_output(handover_result)
    print(f"Throughput after Handover (AP2): {handover_throughput} Mbps")
    print(f"Packet Loss after Handover (AP2): {handover_loss}%")

    # Stop the network
    net.stop()

    # Plotting the results
    labels = ['Before Handover (AP1)', 'After Handover (AP2)']
    throughput_data = [initial_throughput, handover_throughput]
    loss_data = [initial_loss, handover_loss]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

    ax1.bar(labels, throughput_data, color='blue')
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Throughput Before and After Handover')

    ax2.bar(labels, loss_data, color='red')
    ax2.set_ylabel('Packet Loss (%)')
    ax2.set_title('Packet Loss Before and After Handover')

    plt.tight_layout()
    plt.savefig('handover_performance.png')
    plt.show()

if __name__ == '__main__':
    main()
