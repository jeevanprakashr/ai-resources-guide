import math
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline

def f(x):
    return 3*x**2 - 4*x + 5     # a parabolic function

xs = np.arange(-5, 5, 0.25)
ys = f(xs)
plt.plot(xs, ys)
plt.show()