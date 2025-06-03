from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time
import matplotlib.pyplot as plt
import re

def setup_network():
    """Set up network with two Access Points and one mobile station."""
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', position='20,30,0')  # Near AP1 initially
    ap1 = net.addAccessPoint('ap1', ssid='wifi-network', mode='g', channel='1', position='50,30,0')
    ap2 = net.addAccessPoint('ap2', ssid='wifi-network', mode='g', channel='1', position='150,30,0')
    c0 = net.addController('c0')

    info("*** Configuring WiFi nodes\n")
    net.configureWifiNodes()
    net.plotGraph(max_x=200, max_y=60)
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])

    return net, sta1, ap1, ap2

def start_udp_server(ap, filename):
    """Start UDP iperf server."""
    ap.cmd(f'iperf -s -u -i 1 > {filename} &')
    time.sleep(1)

def start_udp_client(sta, ap_ip):
    """Start UDP iperf client to simulate video streaming."""
    info(f"*** Starting video streaming to {ap_ip}\n")
    result = sta.cmd(f'iperf -c {ap_ip} -u -b 5M -t 20 -i 1')
    return result

def reduce_signal_strength(ap):
    """Reduce signal strength of AP to force handover."""
    info("*** Reducing signal strength of AP1\n")
    ap.cmd('iw dev ap1-wlan1 set txpower fixed 1000')  # 1000 = 10 dBm
    time.sleep(5)

def move_station(sta, new_position):
    """Move station to simulate mobility/handover."""
    info(f"*** Moving station to {new_position}\n")
    sta.setPosition(new_position)
    time.sleep(5)

def parse_iperf_output(output):
    """Extract average throughput, packet loss, and latency from iperf output."""
    throughput_values = []
    loss_pct = 0.0
    latency_ms = 0.0

    for line in output.splitlines():
        if 'Mbits/sec' in line:
            match = re.search(r'(\d+\.?\d*)\s+Mbits/sec', line)
            if match:
                throughput_values.append(float(match.group(1)))
        if 'datagrams' in line and 'loss' in line:
            match = re.search(r'(\d+)%\s+loss', line)
            if match:
                loss_pct = float(match.group(1))
        if 'ms' in line:
            match = re.search(r'(\d+\.?\d*)\s+ms', line)
            if match:
                latency_ms = float(match.group(1))

    avg_throughput = sum(throughput_values) / len(throughput_values) if throughput_values else 0.0
    return avg_throughput, loss_pct, latency_ms

def measure_video_streaming_during_handover():
    """Main experiment: simulate handover and collect video streaming performance metrics."""
    net, sta1, ap1, ap2 = setup_network()

    # Start iperf servers
    start_udp_server(ap1, '/tmp/ap1_video.txt')
    start_udp_server(ap2, '/tmp/ap2_video.txt')

    # Stream video from AP1
    ap1_ip = ap1.IP()
    info("*** Testing video streaming with AP1\n")
    initial_result = start_udp_client(sta1, ap1_ip)

    # Reduce AP1 signal to force handover
    reduce_signal_strength(ap1)
    disconnect_time = time.time()

    # Move station near AP2
    move_station(sta1, '150,30,0')
    reconnect_time = time.time()
    handover_time = reconnect_time - disconnect_time

    # Stream video from AP2
    ap2_ip = ap2.IP()
    info("*** Testing video streaming with AP2\n")
    handover_result = start_udp_client(sta1, ap2_ip)

    # Stop network
    net.stop()

    # Parse results
    initial_tput, initial_loss, initial_latency = parse_iperf_output(initial_result)
    handover_tput, handover_loss, handover_latency = parse_iperf_output(handover_result)

    print(f"\n=== Handover Time: {handover_time:.2f} seconds ===")
    print(f"Initial (AP1) Throughput: {initial_tput:.2f} Mbps")
    print(f"Initial (AP1) Packet Loss: {initial_loss:.2f}%")
    print(f"Initial (AP1) Latency: {initial_latency:.2f} ms")
    print(f"Handover (AP2) Throughput: {handover_tput:.2f} Mbps")
    print(f"Handover (AP2) Packet Loss: {handover_loss:.2f}%")
    print(f"Handover (AP2) Latency: {handover_latency:.2f} ms")

    # Plot results
    labels = ['Before Handover (AP1)', 'After Handover (AP2)']
    throughputs = [initial_tput, handover_tput]
    losses = [initial_loss, handover_loss]
    latencies = [initial_latency, handover_latency]

    fig, axs = plt.subplots(3, 1, figsize=(8, 10))
    axs[0].bar(labels, throughputs, color='green')
    axs[0].set_ylabel('Throughput (Mbps)')
    axs[0].set_title(f'Throughput\nHandover Time: {handover_time:.2f} sec')

    axs[1].bar(labels, losses, color='red')
    axs[1].set_ylabel('Packet Loss (%)')
    axs[1].set_title('Packet Loss')

    axs[2].bar(labels, latencies, color='blue')
    axs[2].set_ylabel('Latency (ms)')
    axs[2].set_title('Latency')

    plt.tight_layout()
    plt.savefig('forced_handover_video_streaming.png')
    plt.show()

if __name__ == '__main__':
    setLogLevel('info')
    measure_video_streaming_during_handover()
