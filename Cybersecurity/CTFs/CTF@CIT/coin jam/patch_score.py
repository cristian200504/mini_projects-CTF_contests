import ctypes
from ctypes import wintypes
import subprocess

PROCESS_ALL_ACCESS = 0x1F0FFF

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)

kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

def get_process_id(name):
    output = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {name}" /NH', shell=True).decode()
    for line in output.split('\n'):
        if name in line:
            return int(line.split()[1])
    return None

def get_base_address(pid):
    h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not h_process:
        return None
    
    h_mods = (wintypes.HMODULE * 1024)()
    cb_needed = wintypes.DWORD()
    if psapi.EnumProcessModules(h_process, ctypes.byref(h_mods), ctypes.sizeof(h_mods), ctypes.byref(cb_needed)):
        base = h_mods[0]
        kernel32.CloseHandle(h_process)
        return base
    kernel32.CloseHandle(h_process)
    return None

def write_score(pid, base, score):
    h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not h_process:
        return False
        
    score_addr = base + 0x1d01c
    score_val = ctypes.c_int32(score)
    bytes_written = ctypes.c_size_t(0)
    
    res = kernel32.WriteProcessMemory(h_process, ctypes.c_void_p(score_addr), ctypes.byref(score_val), ctypes.sizeof(score_val), ctypes.byref(bytes_written))
    kernel32.CloseHandle(h_process)
    return res

if __name__ == '__main__':
    pid = get_process_id('coinjam.exe')
    if pid:
        base = get_base_address(pid)
        print(f"Base: {hex(base)}")
        if write_score(pid, base, 10):
            print("Successfully wrote score!")
        else:
            print("Failed to write score.")
    else:
        print("Not running.")
