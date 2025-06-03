from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time
import matplotlib.pyplot as plt

def setup_network():
    """Set up network with three Access Points and one mobile station."""
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', position='20,30,0')
    ap1 = net.addAccessPoint('ap1', ssid='wifi-network', mode='g', channel='1', position='50,30,0')
    ap2 = net.addAccessPoint('ap2', ssid='wifi-network', mode='g', channel='1', position='100,30,0')
    ap3 = net.addAccessPoint('ap3', ssid='wifi-network', mode='g', channel='1', position='150,30,0')
    c0 = net.addController('c0')

    net.configureWifiNodes()
    net.plotGraph(max_x=200, max_y=60)
    net.build()
    c0.start()
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    return net, sta1, ap1, ap2, ap3

def start_video_streaming(sta1, ap, duration=10):
    """Simulate video streaming using UDP iperf traffic."""
    ap.cmd('killall -9 iperf')  # Make sure previous iperf is killed
    info("*** Starting iperf UDP server on AP\n")
    ap.cmd('iperf -s -u -i 1 > /tmp/ap_video_stream.txt &')
    time.sleep(1)

    info("*** Starting iperf UDP client on sta1\n")
    result = sta1.cmd(f'iperf -c {ap.IP()} -u -b 5M -t {duration} -i 1')
    return result

def move_station(sta1, new_position):
    """Move the station to a new position."""
    info(f"*** Moving station to {new_position}\n")
    sta1.setPosition(new_position)
    time.sleep(5)

def parse_iperf_output(output):
    """Extract throughput, packet loss, and latency from iperf output."""
    throughput = 0.0
    packet_loss = 0.0
    latency = 0.0
    for line in output.splitlines():
        if "Mbits/sec" in line and "Server Report" not in line:
            try:
                throughput = float(line.split()[-2])
            except:
                continue
        if "%" in line and "loss" in line:
            try:
                packet_loss = float(line.split()[6].strip('%'))
            except:
                continue
        if "ms" in line:
            try:
                latency = float(line.split()[4].strip('ms'))
            except:
                continue
    return throughput, packet_loss, latency

def measure_video_streaming_during_roaming():
    net, sta1, ap1, ap2, ap3 = setup_network()

    # Streaming from AP1
    info("*** Streaming from AP1\n")
    result_ap1 = start_video_streaming(sta1, ap1)

    # Move to AP2
    move_station(sta1, '100,30,0')
    info("*** Streaming from AP2\n")
    result_ap2 = start_video_streaming(sta1, ap2)

    # Move to AP3
    move_station(sta1, '150,30,0')
    info("*** Streaming from AP3\n")
    result_ap3 = start_video_streaming(sta1, ap3)

    net.stop()

    # Parse results
    ap1_throughput, ap1_loss, ap1_latency = parse_iperf_output(result_ap1)
    ap2_throughput, ap2_loss, ap2_latency = parse_iperf_output(result_ap2)
    ap3_throughput, ap3_loss, ap3_latency = parse_iperf_output(result_ap3)

    # Print results
    print(f"\n=== Video Streaming Performance ===")
    print(f"AP1 -> Throughput: {ap1_throughput} Mbps, Loss: {ap1_loss}%, Latency: {ap1_latency} ms")
    print(f"AP2 -> Throughput: {ap2_throughput} Mbps, Loss: {ap2_loss}%, Latency: {ap2_latency} ms")
    print(f"AP3 -> Throughput: {ap3_throughput} Mbps, Loss: {ap3_loss}%, Latency: {ap3_latency} ms")

    # Plot results
    labels = ['AP1', 'AP2', 'AP3']
    throughput_data = [ap1_throughput, ap2_throughput, ap3_throughput]
    loss_data = [ap1_loss, ap2_loss, ap3_loss]
    latency_data = [ap1_latency, ap2_latency, ap3_latency]

    fig, axs = plt.subplots(3, 1, figsize=(8, 12))
    axs[0].bar(labels, throughput_data, color='green')
    axs[0].set_title('Throughput (Mbps)')
    axs[1].bar(labels, loss_data, color='red')
    axs[1].set_title('Packet Loss (%)')
    axs[2].bar(labels, latency_data, color='blue')
    axs[2].set_title('Latency (ms)')
    for ax in axs: ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig('multi_ap_roaming_performance.png')
    plt.show()

if __name__ == '__main__':
    setLogLevel('info')
    measure_video_streaming_during_roaming()
