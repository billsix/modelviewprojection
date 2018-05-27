#Copyright (c) 2018 William Emerison Six
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import numpy as np
import matplotlib.pyplot as plt
import math
import sys
import itertools

import generategridlines
import mpltransformations as mplt


if __name__ != "__main__":
    sys.exit(0)

import doctest
modules = [mplt]
for m in modules:
    try:
        doctest.testmod(m,
                        raise_on_error=True)
        print(doctest.testmod(m))
    except Exception:
        print("foo")
        print(doctest.testmod())
        sys.exit(1)


## Translation Plots


## Translation Plots - reading the transformations forward

### Step 1
graphBounds = (100,100)

fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])



#plot natural basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = xs,ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))



# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame1.png')
plt.close(fig)





### Step 2

graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(-90.0,
                                                      0.0,
                                                      xs,
                                                      ys))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame2.png')
plt.close(fig)



### Step 3


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(0.0,
                                                      20.0,
                                                      *mplt.translate(-90.0,
                                                                      0.0,
                                                                      xs,
                                                                      ys)))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame3.png')
plt.close(fig)


### Step 3.5

graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(0.0,
                                                      20.0,
                                                      *mplt.translate(-90.0,
                                                                      0.0,
                                                                      xs,
                                                                      ys)))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame3.5.png')
plt.close(fig)






### Step 4


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = xs,ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame4.png')
plt.close(fig)




### Step 5


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(90.0,
                                                 0.0,
                                                 xs,
                                                 ys)
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame5.png')
plt.close(fig)



### Step 6


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(0.0,
                                                 -40.0,
                                                 *mplt.translate(90.0,
                                                                 0.0,
                                                                 xs,
                                                                 ys))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame6.png')
plt.close(fig)


### Step 6.5


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

paddleXs, paddleYs = mplt.translate(0.0,
                                    -40.0,
                                    *mplt.translate(90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))

plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(1.0, 0.0, 0.0))


# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(0.0,
                                                 -40.0,
                                                 *mplt.translate(90.0,
                                                                 0.0,
                                                                 xs,
                                                                 ys))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame6.5.png')
plt.close(fig)




### Step 7


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

paddleXs, paddleYs = mplt.translate(0.0,
                                    -40.0,
                                    *mplt.translate(90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))

plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(1.0, 0.0, 0.0))


# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = xs, ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame7.png')
plt.close(fig)



### Step 8


graphBounds = (1,1)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.scale(1.0/100.0,
                                1.0/100.0,
                                *mplt.translate(0.0,
                                                20.0,
                                                *mplt.translate(-90.0,
                                                                0.0,
                                                                *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

paddleXs, paddleYs = mplt.scale(1.0/100.0,
                                1.0/100.0,
                                *mplt.translate(0.0,
                                                -40.0,
                                                *mplt.translate(90.0,
                                                                0.0,
                                                                *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))

plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(1.0, 0.0, 0.0))


# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=1):
   transformedXs, transformedYs = xs, ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFrame8.png')
plt.close(fig)



## Translation Plots - reading the transformations forward

### Step 1
graphBounds = (100,100)

fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])



#plot natural basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = xs,ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))



# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards1.png')
plt.close(fig)





### Step 2

graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(0.0,
                                                      20.0,
                                                      xs,
                                                      ys))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards2.png')
plt.close(fig)



### Step 3


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(-90.0,
                                                      0.0,
                                                      *mplt.translate(0.0,
                                                                      20.0,
                                                                      xs,
                                                                      ys)))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards3.png')
plt.close(fig)


### Step 3.5

graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(-90.0,
                                                      0.0,
                                                      *mplt.translate(0.0,
                                                                      20.0,
                                                                      xs,
                                                                      ys)))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards3.5.png')
plt.close(fig)






### Step 4


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = xs,ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards4.png')
plt.close(fig)




### Step 5


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(0.0,
                                                 -40.0,
                                                 xs,
                                                 ys)
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards5.png')
plt.close(fig)



### Step 6


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(90.0,
                                                 0.0,
                                                 *mplt.translate(0.0,
                                                                 -40.0,
                                                                 xs,
                                                                 ys))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards6.png')
plt.close(fig)


### Step 6.5


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

paddleXs, paddleYs = mplt.translate(0.0,
                                    -40.0,
                                    *mplt.translate(90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))

plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(1.0, 0.0, 0.0))


# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(90.0,
                                                 0.0,
                                                 *mplt.translate(0.0,
                                                                 -40.0,
                                                                 xs,
                                                                 ys))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards6.5.png')
plt.close(fig)




### Step 7


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

paddleXs, paddleYs = mplt.translate(0.0,
                                    -40.0,
                                    *mplt.translate(90.0,
                                                    0.0,
                                                    *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))

plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(1.0, 0.0, 0.0))


# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = xs, ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards7.png')
plt.close(fig)



### Step 8


graphBounds = (1,1)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.scale(1.0/100.0,
                                1.0/100.0,
                                *mplt.translate(0.0,
                                                20.0,
                                                *mplt.translate(-90.0,
                                                                0.0,
                                                                *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

paddleXs, paddleYs = mplt.scale(1.0/100.0,
                                1.0/100.0,
                                *mplt.translate(0.0,
                                                -40.0,
                                                *mplt.translate(90.0,
                                                                0.0,
                                                                *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))

plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(1.0, 0.0, 0.0))


# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=1):
   transformedXs, transformedYs = xs, ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacePaddleMovingFramebackwards8.png')
plt.close(fig)

















# Rotation
### Step 1
graphBounds = (100,100)

fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])



#plot natural basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = xs,ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))



# #plot different basis
# for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=25):
#    transformedXs, transformedYs = list(mplt.translate(-90.0,
#                                                       0.0,
#                                                       xs,
#                                                       ys))
#    plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.0, 1.0, 0.0, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation.png')
plt.close(fig)





### Step 2

graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(0.0,
                                                      20.0,
                                                      xs,
                                                      ys))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation2.png')
plt.close(fig)


### Step 2.5

graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(0.0,
                                                      20.0,
                                                      *mplt.translate(-90.0,
                                                                      0.0,
                                                                      xs,
                                                                      ys)))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation2.5.png')
plt.close(fig)



### Step 3

graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])

# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = list(mplt.translate(0.0,
                                                      20.0,
                                                      *mplt.translate(-90.0,
                                                                      0.0,
                                                                      *mplt.rotate(math.radians(45.0),
                                                                                   xs,
                                                                                   ys))))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation3.png')
plt.close(fig)




### Step 4


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *mplt.rotate(math.radians(45.0),
                                                                 *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(0.0,
                                                 20.0,
                                                 *mplt.translate(-90.0,
                                                                 0.0,
                                                                 *mplt.rotate(math.radians(45.0),
                                                                              xs,ys)))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation4.png')
plt.close(fig)



### Step 4.5


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *mplt.rotate(math.radians(45.0),
                                                                 *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = xs,ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation4.5.png')
plt.close(fig)




### Step 5


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *mplt.rotate(math.radians(45.0),
                                                                 *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(0.0,
                                                 -40.0,
                                                 xs,
                                                 ys)
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation5.png')
plt.close(fig)



### Step 6


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *mplt.rotate(math.radians(45.0),
                                                                 *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(0.0,
                                                 -40.0,
                                                 *mplt.translate(90.0,
                                                                 0.0,
                                                                 xs,
                                                                 ys))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation6.png')
plt.close(fig)




### Step 7


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *mplt.rotate(math.radians(45.0),
                                                                 *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))



# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(0.0,
                                                 -40.0,
                                                 *mplt.translate(90.0,
                                                                 0.0,
                                                                 *mplt.rotate(math.radians(-10.0),
                                                                              xs,
                                                                              ys)))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation7.png')
plt.close(fig)



### Step 7.5


graphBounds = (100,100)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.translate(0.0,
                                    20.0,
                                    *mplt.translate(-90.0,
                                                    0.0,
                                                    *mplt.rotate(math.radians(45.0),
                                                                 *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

paddleXs, paddleYs = mplt.translate(0.0,
                                    -40.0,
                                    *mplt.translate(90.0,
                                                    0.0,
                                                    *mplt.rotate(math.radians(-10.0),
                                                                 *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]])))))

plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(1.0, 0.0, 0.0))


# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=5):
   transformedXs, transformedYs = mplt.translate(0.0,
                                                 -40.0,
                                                 *mplt.translate(90.0,
                                                                 0.0,
                                                                 *mplt.rotate(math.radians(-10.0),
                                                                              xs,
                                                                              ys)))
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation7.5.png')
plt.close(fig)



### Step 8


graphBounds = (1,1)
fig, axes = plt.subplots()
axes.set_xlim([-graphBounds[0],graphBounds[0]])
axes.set_ylim([-graphBounds[1],graphBounds[1]])
paddleXs, paddleYs = mplt.scale(1.0/100.0,
                                1.0/100.0,
                                *mplt.translate(0.0,
                                                20.0,
                                                *mplt.translate(-90.0,
                                                                0.0,
                                                                *mplt.rotate(math.radians(45.0),
                                                                             *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))))
plt.plot(paddleXs, paddleYs, 'k-', lw=1,  color=(0.578123, 0.0, 1.0))

paddleXs, paddleYs = mplt.scale(1.0/100.0,
                                1.0/100.0,
                                *mplt.translate(0.0,
                                                -40.0,
                                                *mplt.translate(90.0,
                                                                0.0,
                                                                *mplt.rotate(math.radians(-10.0),
                                                                             *zip(*np.array([[-10.0,-30.0],[10.0,-30.0],[10.0,30.0],[-10.0,30.0],[-10.0,-30.0]]))))))

plt.plot(paddleXs, paddleYs, 'k-', lw=1, color=(1.0, 0.0, 0.0))


# #plot different basis
for xs, ys, thickness in generategridlines.generategridlines(graphBounds, interval=1):
   transformedXs, transformedYs = xs, ys
   plt.plot(transformedXs, transformedYs, 'k-', lw=thickness, color=(0.1, 0.2, 0.5, 0.3))

# make sure the x and y axis are equally proportional in screen space
plt.gca().set_aspect('equal', adjustable='box')
fig.savefig('modelspacerotation8.png')
plt.close(fig)
