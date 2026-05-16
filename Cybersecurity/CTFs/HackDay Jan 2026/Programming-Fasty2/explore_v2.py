import socket

HOST = '51.210.244.18'
PORT = 8688

def main():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            print(f"Connecting to F4STY at {HOST}:{PORT}...")
            s.connect((HOST, PORT))
            print("Connected.")
            
            while True:
                try:
                    data = s.recv(4096)
                    if not data:
                        break
                    print(data.decode('utf-8', errors='ignore'), end='', flush=True)
                except socket.timeout:
                    print("\n[Timeout] No more data.")
                    break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
