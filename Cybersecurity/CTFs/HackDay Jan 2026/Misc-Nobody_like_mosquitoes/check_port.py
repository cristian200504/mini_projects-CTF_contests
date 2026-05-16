import socket
import time

def check():
    try:
        s = socket.create_connection(("51.210.244.18", 1883), timeout=5)
        print("Connected to port 1883")
        s.close()
    except Exception as e:
        print(f"Failed: {e}")

check()
