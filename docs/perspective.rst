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


.. figure:: _static/screenshots/frustum2.png
    :align: center
    :alt: Frustum 2
    :figclass: align-center




Scale Camera-space x by Camera-space z
######################################


.. math::
    \begin{bmatrix}
      {x'} \\
      {y'} \\
      {z'} \\
      {w'=1} \\
    \end{bmatrix}  = \vec{f}_{1}(\begin{bmatrix}
                             {x_c} \\
                             {y_c} \\
                             {z_c} \\
                             {w_c=1} \\
                   \end{bmatrix}; nearZ_c)   = \begin{bmatrix}
              {nearZ_c \over {z_c}} & 0 & 0 & 0 \\
              0  &               1 & 0 & 0 \\
              0  &               0 & 1 & 0 \\
              0, &               0 & 0 & 1
                   \end{bmatrix}  *
                    \begin{bmatrix}
                             {x_c} \\
                             {y_c} \\
                             {z_c} \\
                             {w_c=1} \\
                   \end{bmatrix}

resulting in

.. figure:: _static/screenshots/frustum3.png
    :align: center
    :alt: Frustum 3
    :figclass: align-center

    Scale the camera space x by the camera space z


Scale Camera-space y by Camera-space z
######################################


.. math::
    \begin{bmatrix}
      {x''} \\
      {y''} \\
      {z''} \\
      {w''=1} \\
    \end{bmatrix}  =    \vec{f}_{2}(\begin{bmatrix}
                             {x'} \\
                             {y'} \\
                             {z'} \\
                             {w'=1} \\
                   \end{bmatrix}; nearZ_c)  = \begin{bmatrix}
          1 & 0 &                  0 & 0 \\
          0 & {nearZ_c \over {z_c}}    &       0 & 0 \\
          0 & 0 &                  1 & 0 \\
          0 & 0 &                  0 & 1
                   \end{bmatrix}  *
                    \begin{bmatrix}
                             {x'} \\
                             {y'} \\
                             {z'} \\
                             {w'=1} \\
                   \end{bmatrix}

resulting in



.. figure:: _static/screenshots/frustum4.png
    :align: center
    :alt: Frustum 4
    :figclass: align-center

    Scale the camera space y by the cameraspace z


Translate Rectangular Prism's Center to Center
##############################################



midpoint_x = 0 ; // centered on x

midpoint_y = 0 ; // centered on y

midpoint_z = (farZ_c + nearZ_c) / 2.0;


.. math::
    \begin{bmatrix}
      {x'''} \\
      {y'''} \\
      {z'''} \\
      {w'''=1} \\
    \end{bmatrix}  =        \vec{f}_{3}(\begin{bmatrix}
                             {x''} \\
                             {y''} \\
                             {z''} \\
                             {w''=1} \\
                   \end{bmatrix}; farZ_c, nearZ_c)  = \begin{bmatrix}
          1 & 0 & 0 & 0 \\
          0 & 1 & 0 & 0 \\
          0 & 0 & 1 & {-{{farZ_c + nearZ_c} \over 2.0}} \\
          0 & 0 & 0 & 1
                   \end{bmatrix}  *
                    \begin{bmatrix}
                             {x''} \\
                             {y''} \\
                             {z''} \\
                             {w''=1} \\
                   \end{bmatrix}


.. figure:: _static/screenshots/frustum5.png
    :align: center
    :alt: Frustum 5
    :figclass: align-center




Scale by inverse of the dimensions of the Rectangular Prism
###########################################################


float x_length = right * 2;

float y_length = top * 2;

float z_length = farZ_c - nearZ_c;

.. math::
    \begin{bmatrix}
      {x''''} \\
      {y''''} \\
      {z''''} \\
      {w''''=1} \\
    \end{bmatrix}  =           \vec{f}_{4}(\begin{bmatrix}
                             {x'''} \\
                             {y'''} \\
                             {z'''} \\
                             {w'''=1} \\
                   \end{bmatrix}; farZ_c, nearZ_c)  = \begin{bmatrix}
         {1 \over right} &     0 &           0 &                  0 \\
         0 &           {1 \over top} &       0 &                  0 \\
         0 &           0 &           {2.0 \over {nearZ_c - farZ_c}} &   0 \\
         0 &           0 &           0 &                  1
                   \end{bmatrix}  *
                    \begin{bmatrix}
                             {x'''} \\
                             {y'''} \\
                             {z'''} \\
                             {w'''=1} \\
                   \end{bmatrix}

.. figure:: _static/screenshots/frustum6.png
    :align: center
    :alt: Frustum 6
    :figclass: align-center


Premultiply the matricies
#########################


.. math::
    \begin{bmatrix}
      {x_{ndc}} \\
      {y_{ndc}} \\
      {z_{ndc}} \\
      {w_{ndc}=1} \\
    \end{bmatrix}  =           \vec{f}_{4}(\begin{bmatrix}
                             {x''''} \\
                             {y''''} \\
                             {z''''} \\
                             {w''''=1} \\
                   \end{bmatrix}; farZ_c, nearZ_c)
                    = ( \vec{f}_{4} \circ  \vec{f}_{3} \circ \vec{f}_{2} \circ \vec{f}_{1}) \begin{bmatrix}
                             {x_c} \\
                             {y_c} \\
                             {z_c} \\
                             {w_c=1} \\
                   \end{bmatrix}




Multiply them all together to get the following.  The elements of this premultiplied matrix have no geometric
meaning to the author, and that's ok.  The matricies above all of geometric meaning, and we premultiply them
together for computational efficiency, as well as being able to do the next step in clip space, which
we couldn't do without having the premultiplied matrix.

.. math::
    \begin{bmatrix}
      {x_{ndc}} \\
      {y_{ndc}} \\
      {z_{ndc}} \\
      {w_{ndc}=1} \\
    \end{bmatrix}  =               \vec{f}_{c}^{ndc}(\begin{bmatrix}
                             {x_{c}^{ndc}} \\
                             {y_{c}^{ndc}} \\
                             {z_{c}^{ndc}} \\
                             {w_{c}^{ndc}=1} \\
                   \end{bmatrix}; farZ_c, nearZ_c, top, right) = \begin{bmatrix}
                      {nearZ_c \over {right * z}} &             0 &                      0 &                0 \\
                      0 &                           {nearZ_c \over {top*z}} &           0 &                0 \\
                      0 &                           0 &                       {2.0 \over {nearZ_c - farZ_c}} & {-{farZ_c + nearZ_c} \over {nearZ_c - farZ_c}} \\
                      0 &                           0 &                       0 &                1
                   \end{bmatrix} *
                    \begin{bmatrix}
                             {x_{c}^{ndc}} \\
                             {y_{c}^{ndc}} \\
                             {z_{c}^{ndc}} \\
                             {w_{c}^{ndc}=1} \\
                   \end{bmatrix}


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
position the nearZ_c to farZ_c data into NDC. Everything
we've done so far in the class does.  The standard
perspective matrix ends up having less Z-fighting
close to nearZ_c, and more problems with Z-fighting
near farZ_c)


Given that OpenGL accepts clip space, which it itself
will convert to NDC, we here are taking our NDC and turning
it into clip space

.. math::
    \vec{f}_{clip}^{ndc}(\begin{bmatrix}
                             {x_{clip}} \\
                             {y_{clip}} \\
                             {z_{clip}} \\
                             {w_{clip}} \\
                   \end{bmatrix}) =  \begin{bmatrix}
                      {1 \over {w_{clip}}} &  0 & 0 & 0 \\
                      0 &  {1 \over {w_{clip}}} & 0 & 0 \\
                      0 &  0 & {1 \over {w_{clip}}} & 0 \\
                      0 &  0 & 0 & {1 \over {w_{clip}}}
                   \end{bmatrix} *
                     \begin{bmatrix}
                             {x_{clip}} \\
                             {y_{clip}} \\
                             {z_{clip}} \\
                             {w_{clip}}
                   \end{bmatrix}


So to put our NDC data into clip space, knowing what OpenGL is going to do in
the equation above, we need to decide what we want our clip space value, :math:`w` to be,
and do the inverse of the equation above

.. math::
    \vec{f}_{ndc}^{clip}(\begin{bmatrix}
                             {x_{ndc}} \\
                             {y_{ndc}} \\
                             {z_{ndc}} \\
                             {w_{ndc}} \\
                   \end{bmatrix}; w) =  \begin{bmatrix}
                      w &  0 & 0 & 0 \\
                      0 &  w & 0 & 0 \\
                      0 &  0 & w & 0 \\
                      0 &  0 & 0 & w
                   \end{bmatrix} *
                     \begin{bmatrix}
                             {x_{ndc}} \\
                             {y_{ndc}} \\
                             {z_{ndc}} \\
                             {w_{ndc}}
                   \end{bmatrix}


.. math::
    \vec{f}_{clip}^{clip}(\begin{bmatrix}
                             {x_{clip}} \\
                             {y_{clip}} \\
                             {z_{clip}} \\
                             {w_{clip}} \\
                   \end{bmatrix})
                    = ( \vec{f}_{clip}^{ndc} \circ \vec{f}_{ndc}^{clip}) \begin{bmatrix}
                             {x_{clip}} \\
                             {y_{clip}} \\
                             {z_{clip}} \\
                             {w} \\
                   \end{bmatrix}


Since we want to get the :math:`z_c` relative to camera space out of the matrix, we choose
the following

.. math::
    \vec{f}_{ndc}^{clip}(\begin{bmatrix}
                             {x_{ndc}} \\
                             {y_{ndc}} \\
                             {z_{ndc}} \\
                             {w_{ndc}=1} \\
                   \end{bmatrix}; z_c) =  \begin{bmatrix}
                      -z_c &  0 & 0 & 0 \\
                      0 &  -z_c & 0 & 0 \\
                      0 &  0 & -z_c & 0 \\
                      0 &  0 & 0 & -z_c
                   \end{bmatrix} *
                     \begin{bmatrix}
                             {x_{ndc}} \\
                             {y_{ndc}} \\
                             {z_{ndc}} \\
                             {w_{ndc}}
                   \end{bmatrix}



To get camera z out of the matrix, where it's currently in two denominators, we
can use knowledge of clip space, wherein we put cameraspace's z into W.     because cameraSpace's z coordinate is negative, we want to scale
all dimensions without flipping, hence the negative sign in front of :math:`-z_c`.


.. math::
    \vec{f}_{c}^{clip}(\begin{bmatrix}
                             {x'''} \\
                             {y'''} \\
                             {z'''} \\
                             {w'''=1} \\
                   \end{bmatrix}; farZ_c, nearZ_c, top, right) & =  (\vec{f}_{ndc}^{clip} \circ \vec{f}_{4})  *
                    \begin{bmatrix}
                             {x'''} \\
                             {y'''} \\
                             {z'''} \\
                             {w'''=1} \\
                   \end{bmatrix} \\
                   & = \begin{bmatrix}
                             {-nearZ_c \over right} &         0 &        0 &                                   0 \\
                             0 &                  {-nearZ_c \over top} & 0 &                                   0 \\
                             0 &                  0 &        {2.0*(-z_c) \over {nearZ_c - farZ_c}} &   {-z_c*{-{farZ_c + nearZ_c} \over {nearZ_c - farZ_c}}} \\
                             0 &                  0 &        0 &                                   -z_c
                   \end{bmatrix} *
                    \begin{bmatrix}
                             {x'''} \\
                             {y'''} \\
                             {z'''} \\
                             {w'''=1} \\
                   \end{bmatrix}


The result of this is in clip space, where for the first time, our w component is not 1, but :math:`-z_c`.

Knowing that OpenGL will turn our clip space data back to NDC, let's verify that after dividing :math:`c_z` by :math:`c_w`, that :math:`nearZ_c` maps to :math:`-1`
and that :math:`farZ_c` maps to :math:`1`.


For a given :math:`z`

.. math::
    {{clip_z} \over {clip_w}} & =  {{{z * {{2.0*{-z_c}} \over {nearZ_c - farZ_c}}} +   {-z_c}*{{-{farZ_c + nearZ_c} \over {nearZ_c - farZ_c}}}} \over {z}} \\
                      & = 2.0*{{-z_c} \over {nearZ_c - farZ_c}} +   {{farZ_c + nearZ_c} \over {nearZ_c - farZ_c}}

Calculating that out for :math:`nearZ_c`

.. math::
    {{clip_z} \over {clip_w}} & = 2.0*{-nearZ_c \over {nearZ_c - farZ_c}} +   {{{farZ_c + nearZ_c}} \over  {nearZ_c - farZ_c}} \\
                      & = {{2.0*{-nearZ_c} + {farZ_c + nearZ_c}} \over {nearZ_c - farZ_c}} \\
                      & = {{2.0*{-nearZ_c} + {farZ_c + nearZ_c}} \over {nearZ_c - farZ_c}} \\
                      & = {{farZ_c - nearZ_c} \over {nearZ_c - farZ_c}} \\
                      & = {{farZ_c - nearZ_c} \over {nearZ_c - farZ_c}} \\
                      & = -1

Calculating that out for :math:`farZ_c`

.. math::
    {clip_z} \over {clip_w} & = 2.0* {{-nearZ_c} \over {nearZ_c - farZ_c}} +   {{farZ_c + nearZ_c} \over {nearZ_c - farZ_c}} \\
                      & =  2.0*{{-farZ_c} \over {nearZ_c - farZ_c}} +   {{farZ_c + nearZ_c} \over {nearZ_c - farZ_c}} \\
                      & = {{2.0*-farZ_c + farZ_c + nearZ_c} \over {nearZ_c - farZ_c}} \\
                      & = {{ nearZ_c - farZ_c} \over {nearZ_c - farZ_c}} \\
                      & = 1
