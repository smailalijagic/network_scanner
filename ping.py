import socket
import subprocess
import re
import threading
import queue

"""
A simple python script to discover devices (via ping) connected to the same local network.
Mobile devices can be found easily, while many computers have built-in mechanism which are enabled per default.
"""

def get_local_ip():
    try:
        # works only on mac: ipconfig getifaddr en0
        os_call = subprocess.run(
            ["ipconfig", "getifaddr", "en0"],
            capture_output=True,
            text=True
        )
        return os_call.stdout.strip()
    except:
        return "127.0.0.1"


def get_network_range(my_ip):
    parts = my_ip.split(".")
    return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

def ping_single_ip(ip):
    command = ["ping", "-c", "1", ip]
    try:
        res = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        return (res.returncode == 0, ip)
    except:
        return (False, ip)


def ping_ip_range(ip_range):
    base_ip = ip_range.split("/")[0].rsplit(".", 1)[0]
    
    results_queue = queue.Queue()
    active_hosts = []
    
    def worker(ip):
        is_active, ip_addr = ping_single_ip(ip)
        results_queue.put((is_active, ip_addr))
    
    # Start all threads
    threads = []

    for i in range(1, 255):
        ip = f"{base_ip}.{i}"
        thread = threading.Thread(target=worker, args=(ip,))
        thread.start()
        threads.append(thread)
    
    # Collect results as they come in
    print("      hostname       |        ip        |     mac_addr    ")
    print("-" * 61)
    
    completed = 0
    while completed < 254:
        try:
            is_active, ip = results_queue.get(timeout=0.1)
            completed += 1
            if is_active:
                active_hosts.append(ip)
                hostname = get_hostname(ip)
                mac = get_mac_addr(ip)
                print(f"{hostname:<20} | {ip:<16} | {mac:<16}")
        except:
            pass
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    return active_hosts

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "Unknown"

def get_mac_addr(ip):
    try:
        output = subprocess.check_output(f"arp {ip}", shell=True).decode()
        mac = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", output)
        if mac:
            return mac.group(0)
        return "Unknown"
    except:
        return "Unknown"

def main():
    print("\n" + "=" * 61)
    print(" " * 20 + "Local Network Scanner" + " " * 20)
    print("=" * 61 + "\n")
    
    my_ip = get_local_ip()
    network_range = get_network_range(my_ip)
    
    print(f"Your IP: {my_ip}")
    print(f"Network Range: {network_range}\n")
    
    active_hosts = ping_ip_range(network_range)
    
    print("\n" + "=" * 61)
    print(f"Found {len(active_hosts)} device(s)")
    print("=" * 61)


if __name__ == "__main__":
    main()