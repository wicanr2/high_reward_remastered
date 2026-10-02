import sys
import numpy as np
from PIL import Image
a = np.array(Image.open(sys.argv[1]).convert("RGBA")).astype(int)
b = np.array(Image.open(sys.argv[2]).convert("RGBA")).astype(int)
d = np.abs(a - b)
print("shape", a.shape, b.shape, "max diff", d.max(), "mean", d.mean(), "n>2", int((d.max(-1) > 2).sum()))
