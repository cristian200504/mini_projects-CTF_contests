import numpy as np
from PIL import Image

# Read binary VRAM dump
data = open('vram_dump.bin', 'rb').read()

# Metadata found via strings:
# &tensor_shape=(1,3,512,512)
# dtype=float16
# buffer_addr=0x00900000
# layout=NCHW

offset = 0x00900000
size = 3 * 512 * 512 * 2

buffer = data[offset : offset + size]
tensor = np.frombuffer(buffer, dtype=np.float16).reshape(3, 512, 512)

# Convert from NCHW to HWC for image saving
tensor_hwc = np.transpose(tensor, (1, 2, 0))

# The tensor contains exactly -1.0 and 1.0, map to 0 and 255
img_data = (tensor_hwc > 0).astype(np.uint8) * 255
img = Image.fromarray(img_data)
img.save('extracted_flag.png')
print('Saved extracted_flag.png')

