import pathlib
b=pathlib.Path(r"c:\Users\crist\OneDrive\Desktop\signal interference\challenge\challenge.iso").read_bytes()
s=b.decode('latin1')
letters=[c for c in s if c.isalpha()]
bits=[1 if c.isupper() else 0 for c in letters]
# use rev=False, shift=1 from scan
cut=bits[1:]
cut=cut[:len(cut)//8*8]
data=bytes(int(''.join(str(x) for x in cut[i:i+8]),2) for i in range(0,len(cut),8))
path=pathlib.Path(r"c:\Users\crist\OneDrive\Desktop\signal interference\challenge\hidden_u1_shift1.bin")
path.write_bytes(data)
print('wrote',path,'len',len(data),'head',data[:8])
print('mz at',data.find(b'MZ'))
