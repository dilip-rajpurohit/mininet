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
    sta1 = net.addStation('sta1', position='10,30,0')  # Initially near AP1
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

def start_video_streaming(sta1, ap, ap_ip):
    """Simulate video streaming by starting a UDP-based stream with iperf."""
    info("*** Starting video streaming (UDP) server on AP\n")
    ap.cmd('killall -9 iperf')  # Clean up old servers
    ap.cmd('iperf -s -u -i 1 > /tmp/video_stream_server.txt &')
    time.sleep(1)

    info("*** Starting video streaming (UDP) client on sta1\n")
    result = sta1.cmd(f'iperf -c {ap_ip} -u -b 5M -t 30 -i 1')
    return result

def move_station(sta1, new_position):
    """Move the station to simulate handover between AP1 and AP2."""
    info(f"*** Moving station to {new_position}\n")
    sta1.setPosition(new_position)
    time.sleep(5)  # Allow time for handover

def measure_video_streaming_during_handover():
    """Measure video streaming performance during AP handover."""
    net, sta1, ap1, ap2 = setup_network()

    # Start video streaming before handover
    info("*** Running video streaming with AP1\n")
    ap1_ip = ap1.IP()
    initial_result = start_video_streaming(sta1, ap1, ap1_ip)

    # Simulate handover
    disconnect_time = time.time()
    move_station(sta1, '150,30,0')  # Move to AP2's area
    reconnect_time = time.time()

    # Start video streaming after handover
    info("*** Running video streaming with AP2\n")
    ap2_ip = ap2.IP()
    handover_result = start_video_streaming(sta1, ap2, ap2_ip)

    handover_time = reconnect_time - disconnect_time
    print(f"\n>>> Handover Time: {handover_time:.2f} seconds")

    net.stop()

    # Parse iperf output
    def parse_iperf_output(output):
        throughput = 0.0
        for line in output.splitlines():
            if 'Mbits/sec' in line:
                try:
                    throughput = float(line.split()[-2])
                except ValueError:
                    continue
        return throughput

    # Extract metrics
    initial_throughput = parse_iperf_output(initial_result)
    handover_throughput = parse_iperf_output(handover_result)

    print(f"Initial Throughput (AP1): {initial_throughput:.2f} Mbps")
    print(f"Throughput after Handover (AP2): {handover_throughput:.2f} Mbps")

    # Plot results
    labels = ['Before Handover', 'After Handover']
    values = [initial_throughput, handover_throughput]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, values, color=['green', 'blue'])
    plt.ylabel('Throughput (Mbps)')
    plt.title(f'UDP Video Streaming Throughput\nHandover Time: {handover_time:.2f} seconds')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('video_streaming_handover.png')
    plt.show()

if __name__ == '__main__':
    setLogLevel('info')
    measure_video_streaming_during_handover()
