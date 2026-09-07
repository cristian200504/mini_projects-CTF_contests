from pathlib import Path
import sys

P = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\santey\Desktop\NNS CTF\dot-matrix\misc_dot-matrix\as1130.logicdata")
b = P.read_bytes()

def dump(off, n=128):
    for i in range(off, min(len(b), off+n), 16):
        print(f"{i:08x}  {b[i:i+16].hex(' ')}")

if __name__ == '__main__':
    dump(int(sys.argv[2],0) if len(sys.argv)>2 else 0, int(sys.argv[3],0) if len(sys.argv)>3 else 512)
