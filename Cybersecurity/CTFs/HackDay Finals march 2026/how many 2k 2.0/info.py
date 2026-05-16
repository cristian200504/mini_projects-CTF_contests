from PIL import Image
import numpy as np

img = Image.open('m4tr1x.png')
arr = np.array(img)
print("Shape:", arr.shape)
if len(arr.shape) == 3:
    unique_colors = len(np.unique(arr.reshape(-1, arr.shape[2]), axis=0))
    print("Unique colors:", unique_colors)
else:
    unique_colors = len(np.unique(arr))
    print("Unique colors:", unique_colors)
