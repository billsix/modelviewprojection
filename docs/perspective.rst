..
   Copyright (c) 2018-2022 William Emerison Six

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.

Standard Perspective Matrix
===========================

Purpose
^^^^^^^

Derive the standard perspective matrix that OpenGL expects.



Description
^^^^^^^^^^^


.. figure:: _static/perspective.png
    :align: center
    :alt: Demo 11
    :figclass: align-center

    Turn our NDC into Clip Space


Matrix form of perspective projection
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&


cameraSpace visible range for .x [-right/((-nearZ)/-cameraSpace.z), (right/(-nearZ)/-cameraSpace.z)]
cameraSpace visible range for .y [-top/((-nearZ)/-cameraSpace.z), top/((-nearZ)/-cameraSpace.z)]
cameraSpace visible range for .z [near,far]


.. math::
    \begin{equation}
    \vec{f}_{c}^{scaled\_x}(\begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}; nearZ)  = \begin{bmatrix}
              nearZ/{c_z} & 0.0 & 0.0 & 0.0 \\
              0.0  &               1.0 & 0.0 & 0.0 \\
              0.0  &               0.0 & 1.0 & 0.0 \\
              0.0, &               0.0 & 0.0 & 1.0
                   \end{bmatrix}  *
                    \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}
    \end{equation}

scale_x visible range for .x [-right, right]
scale_x visible range for .y [-top/((-nearZ)/(-{c_z})), top/((-nearZ)/(-{c_z}))]
scale_z visible range for .z [near,far]

.. math::
    \begin{equation}
    \vec{f}_{c}^{scaled\_y}(\begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}; nearZ)  = \begin{bmatrix}
          1.0 & 0.0 &                  0.0 & 0.0 \\
          0.0 & nearZ/{c_z}    &       0.0 & 0.0 \\
          0.0 & 0.0 &                  1.0 & 0.0 \\
          0.0 & 0.0 &                  0.0 & 1.0
                   \end{bmatrix}  *
                    \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}
    \end{equation}


scale_y visible range for .x [-right,right]
scale_y visible range for .y [-top,top]
scale_y visible range for .z [near,far]




midpoint_x = 0.0 ; // centered on x
midpoint_y = 0.0 ; // centered on y
midpoint_z = (farZ + nearZ) / 2.0;


.. math::
    \begin{equation}
    \vec{f}_{c}^{centered}(\begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}; farZ, nearZ)  = \begin{bmatrix}
          1.0 & 0.0 & 0.0 & 0.0 \\
          0.0 & 1.0 & 0.0 & 0.0 \\
          0.0 & 0.0 & 1.0 & -((farZ + nearZ) / 2.0) \\
          0.0 & 0.0 & 0.0 & 1.0
                   \end{bmatrix}  *
                    \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}
    \end{equation}



float x_length = right * 2;
float y_length = top * 2;
float z_length = farZ - nearZ;

.. math::
    \begin{equation}
    \vec{f}_{c}^{ndc}(\begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}; farZ, nearZ)  = \begin{bmatrix}
         1.0/right &     0.0 &           0.0 &                  0.0 \\
         0.0 &           1.0/top &       0.0 &                  0.0 \\
         0.0 &           0.0 &           2.0/(nearZ - farZ) &   0.0 \\
         0.0 &           0.0 &           0.0 &                  1.0
                   \end{bmatrix}  *
                    \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}
    \end{equation}

.. math::
    \begin{equation}
    \vec{f}_{c}^{ndc}(\begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}; farZ, nearZ)
                    = ( \vec{f}_{c}^{ndc} \circ  \vec{f}_{c}^{centered} \circ \vec{f}_{c}^{scaled\_y} \circ \vec{f}_{c}^{scaled\_x}) \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}
    \end{equation}

Multiply them all together to get

.. math::
    \begin{equation}
    \vec{f}_{c}^{ndc}(\begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}; farZ, nearZ, top, right) = \begin{bmatrix}
                      nearZ/(right * z_c)&             0.0 &                      0.0 &                0.0 \\
                      0.0 &                           nearZ/(top*z_c) &           0.0 &                0.0 \\
                      0.0 &                           0.0 &                       2.0/(nearZ - farZ) & -(farZ + nearZ)/(nearZ - farZ) \\
                      0.0 &                           0.0 &                       0.0 &                1.0
                   \end{bmatrix} *
                    \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}
    \end{equation}


Clip Space
&&&&&&&&&&

convert the data from NDC to clip-space.

We have never used clip-space in the class, only NDC,
because 4D space is confusing geometrically, nevermind
the fact that (NDCx NDCy NDCz) = (Clipx/Clipw, Clipy/Clipy, Clipz/Clipz)

The purpose of going to clip space is that eventually we will be
able to remove the camera space's z coordinate from the matrix.

This will allow us to use one perspective projection matrix for
all vertices, independent of the z coordinate of each input vertex.

I assume, without any evidence to support me, that this
was done for efficiency reasons.
(Side note, the standard perspective projection matrix,
which we will get to by demo 25, does not linearly
position the nearZ to farZ data into NDC. Everything
we've done so far in the class does.  The standard
perspective matrix ends up having less Z-fighting
close to nearZ, and more problems with Z-fighting
near farZ)


Given that OpenGL accepts clip space, which it itself
will convert to NDC, we here are taking our NDC and turning
it into clip space

.. math::
    \begin{equation}
    \vec{f}_{clip}^{ndc}(\begin{bmatrix}
                             {x_{clip}} \\
                             {y_{clip}} \\
                             {z_{clip}}, \\
                             {w_{clip}}, \\
                   \end{bmatrix}) =  \begin{bmatrix}
                      1/{w_{clip}} &  0.0 & 0.0 & 0.0 \\
                      0.0 &  1/{w_{clip}} & 0.0 & 0.0 \\
                      0.0 &  0.0 & 1/{w_{clip}} & 0.0 \\
                      0.0 &  0.0 & 0.0 & 1/{w_{clip}}
                   \end{bmatrix} *
                     \begin{bmatrix}
                             {x_{clip}}, \\
                             {y_{clip}}, \\
                             {z_{clip}}, \\
                             {w_{clip}}
                   \end{bmatrix}
    \end{equation}


So to put our NDC data into clip space, knowing what OpenGL is going to do in
the equation above, we need to decide what we want our clip space value to be,
and do the inverse of the equation above

.. math::
    \begin{equation}
    \vec{f}_{ndc}^{clip}(\begin{bmatrix}
                             {x_{ndc}} \\
                             {y_{ndc}} \\
                             {z_{ndc}}, \\
                             {w_{ndc}}, \\
                   \end{bmatrix}; w) =  \begin{bmatrix}
                      w &  0.0 & 0.0 & 0.0 \\
                      0.0 &  w & 0.0 & 0.0 \\
                      0.0 &  0.0 & w & 0.0 \\
                      0.0 &  0.0 & 0.0 & w
                   \end{bmatrix} *
                     \begin{bmatrix}
                             {x_{ndc}}, \\
                             {y_{ndc}}, \\
                             {z_{ndc}}, \\
                             {w_{ndc}}
                   \end{bmatrix}
    \end{equation}


.. math::
    \begin{equation}
    \vec{f}_{clip}^{clip}(\begin{bmatrix}
                             {x_{clip}}, \\
                             {y_{clip}}, \\
                             {z_{clip}}, \\
                             {w_{clip}}, \\
                   \end{bmatrix})
                    = ( \vec{f}_{clip}^{ndc} \circ \vec{f}_{ndc}^{clip}) \begin{bmatrix}
                             {x_{clip}}, \\
                             {y_{clip}}, \\
                             {z_{clip}}, \\
                             {w_c}, \\
                   \end{bmatrix}
    \end{equation}


Since we want to get the z relative to camera space out of the matrix, we choose
the following

.. math::
    \begin{equation}
    \vec{f}_{ndc}^{clip}(\begin{bmatrix}
                             {x_{ndc}} \\
                             {y_{ndc}} \\
                             {z_{ndc}}, \\
                             {w_{ndc}=1}, \\
                   \end{bmatrix}) =  \begin{bmatrix}
                      -z_c &  0.0 & 0.0 & 0.0 \\
                      0.0 &  -z_c & 0.0 & 0.0 \\
                      0.0 &  0.0 & -z_c & 0.0 \\
                      0.0 &  0.0 & 0.0 & -z_c
                   \end{bmatrix} *
                     \begin{bmatrix}
                             {x_{ndc}}, \\
                             {y_{ndc}}, \\
                             {z_{ndc}}, \\
                             {w_{ndc}}
                   \end{bmatrix}
    \end{equation}



To get camera z out of the matrix, where it's currently in two denominators, we
can use knowledge of clip space, wherein we put cameraspace's z into W.     because cameraSpace's z coordinate is negative, we want to scale
all dimensions without flipping, hence the negative sign in front of cameraSpace.z


.. math::
    \begin{equation}
    \begin{split}
    \vec{f}_{c}^{clip}(\begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}; farZ, nearZ, top, right) & =  \vec{f}_{ndc}^{clip} ( \begin{bmatrix}
                      nearZ/(right * z_c)&             0.0 &                      0.0 &                0.0 \\
                      0.0 &                           nearZ/(top*z_c) &           0.0 &                0.0 \\
                      0.0 &                           0.0 &                       2.0/(nearZ - farZ) & -(farZ + nearZ)/(nearZ - farZ) \\
                      0.0 &                           0.0 &                       0.0 &                1.0
                   \end{bmatrix} *
                    \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}) \\
                   & = \begin{bmatrix}
                             -nearZ/right &         0.0 &        0.0 &                                   0.0 \\
                             0.0 &                  -nearZ/top & 0.0 &                                   0.0 \\
                             0.0 &                  0.0 &        2.0*(-c_z)/(nearZ - farZ) &   (-c_z)*(-(farZ + nearZ)/(nearZ - farZ)) \\
                             0.0 &                  0.0 &        0.0 &                                   -c_z
                   \end{bmatrix} *
                    \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}
    \end{split}
    \end{equation}


we had successfully moved cameraSpace.z out of the upper left quadrant, but moved it down
to the lower right.
How can we get rid of it there too?
Since the vector multiplied by this matrix will provide cameraSpace.z as it's third element,
we can change the fourth row as follows

to remove camera.Z from the matrix, all that is left is row 3.

Row three ensures two important properties:

1) fn(nearZ) -> -1.0, and fn(farZ) -> 1.0

2) Ordering is preserved after the function is applied, i.e. monotonicity.  if a < b, then fn(a) < fn(b).

If we can make a function, that like the third row of the matrix, has those properties, we can replace the
third row and remove cameraSpace.z from the matrix.  This was (is) desirable because we do not need
to create a custom pespective matrix per vertex.


[ X X X X ] [c.x, c.y, c.z, 1.0]'  (here the X in the matrix means a value that we don't care about.
[ X X X X ]
[ 0 0 A B ]
[ X X X X ]

clipSpace.z = A* c.z + B * 1.0  (the first column and the second column are zero because z is independent of x and y)
for nearZ, which must map to -1.0,
ndc.z = clipSpace.z / clipSpace.w =   (A * nearZ + B) / nearZ = -1.0
for farZ, which must map to 1.0,
ndc.z = clipSpace.z / clipSpace.w =   (A * farZ + B) / farZ = 1.0

(A * nearZ + B) = -nearZ                                           (1)

(A * farZ + B)  = farZ                                             (2)

B = -nearZ - A * nearZ                                             (3) (from 1)

(A * farZ + -nearZ - A * nearZ)  = farZ                            (4) (from 2 and 3)

(farZ - nearZ)*A  + -nearZ )  = farZ                               (5)

A = (farZ + nearZ)/(farZ-nearZ)                                    (6)

we found A, now substitute that in to get B

(farZ + nearZ)/(farZ-nearZ) * nearZ + B = -nearZ                    (from 1 and 6)

B = -nearZ - (farZ + nearZ)/(farZ-nearZ) * nearZ

B = (-1 - (farZ + nearZ)/(farZ-nearZ)) * nearZ

B = -(1 + (farZ + nearZ)/(farZ-nearZ)) * nearZ

B = -( (farZ-nearZ + (farZ + nearZ))/(farZ-nearZ)) * nearZ

B = -( (2*farZ)/(farZ-nearZ)) * nearZ

B = (-2*farZ*nearZ)/(farZ-nearZ)

now that we have A and B, write down the function, and ensure that it is
monotonic from (nearZ, farZ), inclusive

z_ndc = ((farZ + nearZ)/(farZ-nearZ) * cameraSpace.z +  (-2*farZ*nearZ)/(farZ-nearZ)) / cameraSpace.z

TODO -- proof of monotonicity

NOW OUR PERSPECTIVE MATRIX IS INDEPENDENT OF cameraSpace.z!!!





.. math::
    \begin{equation}
    \vec{f}_{c}^{clip}(\begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}; farZ, nearZ, top, right) = \begin{bmatrix}
                        -nearZ/right &         0.0 &        0.0 &                           0.0 \\
                        0.0 &                  -nearZ/top & 0.0 &                           0.0 \\
                        0.0 &                  0.0 &        (farZ + nearZ)/(farZ-nearZ) &  (-2*farZ*nearZ)/(farZ-nearZ) \\
                        0.0 &                  0.0 &        -1.0 &                          0.0
                   \end{bmatrix} *
                    \begin{bmatrix}
                             {x_c}, \\
                             {y_c}, \\
                             {z_c}, \\
                             {w_c=1}, \\
                   \end{bmatrix}
    \end{equation}



aoeunsth
