import socket
import time
import requests
import threading
import datetime

# --- Type in the IP of your Dashcam ---
DASHCAM_IP = "192.168.42.1"
HTTP_PORT = 80
HEARTBEAT_PORT = 3333
# The Dashcam needs a heartbeat. Interval is roughly 3 seconds
HEARTBEAT_INTERVAL = 3 

def send_http_init():
    """
    Replicates the HTTP GET sequence from the APP.
    This 'wakes up' the camera and syncs the time.
    """
    print(f"[*] Starting HTTP Initialization on {DASHCAM_IP}:{HTTP_PORT}...")
    
    # Generate timestamp
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    
    # The exact sequence of commands given from the APP:
    urls = [
        "/?custom=1&msg_id=1",
        "/?custom=1&msg_id=20",
        "/?custom=1&msg_id=6",
        f"/?custom=1&msg_id=8&param1=time&param2=auto,{current_time}",
        "/?custom=1&msg_id=21",
        f"/?custom=1&msg_id=8&param1=time&param2=auto,{current_time}",
        "/?custom=1&msg_id=19"
    ]

    session = requests.Session()
    
    for path in urls:
        full_url = f"http://{DASHCAM_IP}{path}"
        try:
            print(f"    -> GET {path}")
            session.get(full_url, timeout=2)
        except requests.exceptions.RequestException as e:
            print(f"    [!] HTTP Error on {path}: {e}")

    print("[*] HTTP Initialization Complete.")

def start_heartbeat():
    """
    Maintains the custom TCP connection on Port 3333.
    Sends 'hi', expects 'fuck.'
    """
    print(f"[*] Starting Keep-Alive Heartbeat on {DASHCAM_IP}:{HEARTBEAT_PORT}...")
    
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((DASHCAM_IP, HEARTBEAT_PORT))
                print("    [+] Connected to heartbeat port.")
                
                while True:
                    # Packet 5: Client sends "hi"
                    payload = b'\x68\x69' 
                    s.sendall(payload)
                    
                    # Packet 12: Server responds "fuck."
                    response = s.recv(1024)
                    
                    # Optional: Print response to verify it matches the dump
                    # print(f"    [<] Heartbeat response: {response}") 
                    
                    time.sleep(HEARTBEAT_INTERVAL)
                    
        except Exception as e:
            print(f"    [!] Heartbeat disconnected: {e}. Reconnecting in 3s...")
            time.sleep(3)

if __name__ == "__main__":
    # 1. Run HTTP Init Sequence
    send_http_init()
    
    # 2. Start Heartbeat in a background thread so it runs while you access the RTSP Stream
    t = threading.Thread(target=start_heartbeat)
    t.daemon = True # This ensures the thread closes when you close the script
    t.start()
    
    print("\n" + "="*50)
    print("CONNECTION ESTABLISHED")
    print("You can now open VLC and connect to:")
    print(f"rtsp://{DASHCAM_IP}/stream0/svc0//")
    print("Leave this window OPEN while streaming.")
    print("="*50 + "\n")
    
    # Keep the main script running
    while True:
        time.sleep(1)