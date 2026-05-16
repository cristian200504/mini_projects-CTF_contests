import pathlib
b=pathlib.Path(r"c:\Users\crist\OneDrive\Desktop\signal interference\challenge\challenge.iso").read_bytes()
s=b.decode('latin1')
letters=[c for c in s if c.isalpha()]
mappings={
    'U1':[1 if c.isupper() else 0 for c in letters],
    'L1':[1 if c.islower() else 0 for c in letters],
}
sigs=[(b'UVT{','flag'),(b'PK\x03\x04','zip'),(b'\x1f\x8b\x08','gzip'),(b'BZh','bzip2'),(b'\x89PNG\r\n\x1a\n','png'),(b'ID3','mp3'),(b'\x7fELF','elf'),(b'MZ','mz'),(b'Rar!\x1a\x07\x00','rar')]
for name,bits in mappings.items():
    print(f"\n=== {name} bits {len(bits)}")
    for rev in [False,True]:
        arr=bits[::-1] if rev else bits
        for shift in range(8):
            cut=arr[shift:]
            cut=cut[:len(cut)//8*8]
            data=bytes(int(''.join(str(x) for x in cut[i:i+8]),2) for i in range(0,len(cut),8))
            for sig,label in sigs:
                idx=data.find(sig)
                if idx!=-1:
                    print('hit',label,'rev',rev,'shift',shift,'idx',idx)
            if b'UVT' in data:
                i=data.find(b'UVT')
                print('contains UVT rev',rev,'shift',shift,'at',i,data[i:i+80])
