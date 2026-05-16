import ctypes
from ctypes import wintypes
import subprocess

# Constants
PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

MEM_COMMIT = 0x1000
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_EXECUTE = 0x10
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t]

def get_process_id(name):
    output = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {name}" /NH', shell=True).decode()
    for line in output.split('\n'):
        if name in line:
            return int(line.split()[1])
    return None

def dump_memory(pid):
    h_process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h_process:
        print(f"Failed to open process {pid}")
        return

    address = ctypes.c_void_p(0)
    mbi = MEMORY_BASIC_INFORMATION()
    
    found_flags = set()

    while kernel32.VirtualQueryEx(h_process, address, ctypes.byref(mbi), ctypes.sizeof(mbi)):
        if mbi.State == MEM_COMMIT and (mbi.Protect & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE)):
            buffer = ctypes.create_string_buffer(mbi.RegionSize)
            bytes_read = ctypes.c_size_t(0)
            if kernel32.ReadProcessMemory(h_process, mbi.BaseAddress, buffer, mbi.RegionSize, ctypes.byref(bytes_read)):
                data = buffer.raw[:bytes_read.value]
                start = 0
                while True:
                    idx = data.find(b'CIT{', start)
                    if idx == -1:
                        break
                    end_idx = data.find(b'}', idx)
                    if end_idx != -1 and end_idx - idx < 64:
                        flag = data[idx:end_idx+1]
                        if flag not in found_flags:
                            print(f"Found flag: {flag.decode('ascii', errors='ignore')}")
                            found_flags.add(flag)
                    start = idx + 1
        
        next_addr = (mbi.BaseAddress or 0) + mbi.RegionSize
        if next_addr >= 0x7FFFFFFFFFFF: # user space max
            break
        address = ctypes.c_void_p(next_addr)

    kernel32.CloseHandle(h_process)

if __name__ == '__main__':
    pid = get_process_id('coinjam.exe')
    if pid:
        print(f"Dumping memory for PID {pid}")
        dump_memory(pid)
    else:
        print("Process not found")
