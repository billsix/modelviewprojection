//Copyright (c) 2018-2021 William Emerison Six
//
//Permission is hereby granted, free of charge, to any person obtaining a copy
//of this software and associated documentation files (the "Software"), to deal
//in the Software without restriction, including without limitation the rights
//to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//copies of the Software, and to permit persons to whom the Software is
//furnished to do so, subject to the following conditions:
//
//The above copyright notice and this permission notice shall be included in all
//copies or substantial portions of the Software.
//
//THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//SOFTWARE.

#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 color_in;

uniform mat4 mvMatrix;
uniform float fov;
uniform float aspectRatio;
uniform float nearZ;
uniform float farZ;

out VS_OUT {
  vec4 color;
} vs_out;

vec4 project(vec4 cameraSpace){

    float top = (-nearZ) * tan(fov * 3.14159265358979323846 / 360.0);
    float right = top * aspectRatio;

     //mat4 camera_space_to_clip_space = transpose(mat4(
     //     -nearZ/right,         0.0,        0.0,                                   0.0,
     //     0.0,                  -nearZ/top, 0.0,                                   0.0,
     //     0.0,                  0.0,        2.0*(-cameraSpace.z)/(nearZ - farZ),   (-cameraSpace.z)*(-(farZ + nearZ)/(nearZ - farZ)),
     //     0.0,                  0.0,        0.0,                                   -cameraSpace.z));

     // we had successfully moved cameraSpace.z out of the upper left quadrant, but moved it down
     // to the lower right.
     // How can we get rid of it there too?
     // Since the vector multiplied by this matrix will provide cameraSpace.z as it's third element,
     // we can change the fourth row as follows

     mat4 camera_space_to_clip_space1 = transpose(mat4(
          -nearZ/right,         0.0,        0.0,                                   0.0,
          0.0,                  -nearZ/top, 0.0,                                   0.0,
          0.0,                  0.0,        2.0*(-cameraSpace.z)/(nearZ - farZ),   (-cameraSpace.z)*(-(farZ + nearZ)/(nearZ - farZ)),
          0.0,                  0.0,        -1.0,                                  0.0));
     return camera_space_to_clip_space1 * cameraSpace;

     // to remove camera.Z from the matrix, all that is left is row 3.
     // Row three ensures two important properties:
     //   1) fn(nearZ) -> -1.0, and fn(farZ) -> 1.0
     //   2) Ordering is preserved after the function is applied, i.e. monotonicity.  if a < b, then fn(a) < fn(b).
     // If we can make a function, that like the third row of the matrix, has those properties, we can replace the
     // third row and remove cameraSpace.z from the matrix.  This was (is) desirable because we do not need
     // to create a custom pespective matrix per vertex.

     //  [ X X X X ] [c.x, c.y, c.z, 1.0]'  (here the X in the matrix means a value that we don't care about.
     //  [ X X X X ]
     //  [ 0 0 A B ]
     //  [ X X X X ]

     //  clipSpace.z = A* c.z + B * 1.0  (the first column and the second column are zero because z is independent of x and y)
     //  for nearZ, which must map to -1.0,
     //    ndc.z = clipSpace.z / clipSpace.w =   (A * nearZ + B) / nearZ = -1.0
     //  for farZ, which must map to 1.0,
     //    ndc.z = clipSpace.z / clipSpace.w =   (A * farZ + B) / farZ = 1.0
     //
     //   (A * nearZ + B) = -nearZ                                           (1)
     //   (A * farZ + B)  = farZ                                             (2)
     //
     //   B = -nearZ - A * nearZ                                             (3) (from 1)
     //   (A * farZ + -nearZ - A * nearZ)  = farZ                            (4) (from 2 and 3)
     //   (farZ - nearZ)*A  + -nearZ )  = farZ                               (5)
     //   A = (farZ + nearZ)/(farZ-nearZ)                                    (6)
     //
     //   we found A, now substitute that in to get B
     //
     //  (farZ + nearZ)/(farZ-nearZ) * nearZ + B = -nearZ                    (from 1 and 6)
     //  B = -nearZ - (farZ + nearZ)/(farZ-nearZ) * nearZ
     //  B = (-1 - (farZ + nearZ)/(farZ-nearZ)) * nearZ
     //  B = -(1 + (farZ + nearZ)/(farZ-nearZ)) * nearZ
     //  B = -( (farZ-nearZ + (farZ + nearZ))/(farZ-nearZ)) * nearZ
     //  B = -( (2*farZ)/(farZ-nearZ)) * nearZ
     //  B = (-2*farZ*nearZ)/(farZ-nearZ)
     //
     // now that we have A and B, write down the function, and ensure that it is
     // monotonic from (nearZ, farZ), inclusive

     // z_ndc = ((farZ + nearZ)/(farZ-nearZ) * cameraSpace.z +  (-2*farZ*nearZ)/(farZ-nearZ)) / cameraSpace.z
     // TODO -- proof of monotonicity

     // NOW OUR PERSPECTIVE MATRIX IS INDEPENDENT OF cameraSpace.z!!!
     mat4 camera_space_to_clip_space = transpose(mat4(
          -nearZ/right,         0.0,        0.0,                           0.0,
          0.0,                  -nearZ/top, 0.0,                           0.0,
          0.0,                  0.0,        (farZ + nearZ)/(farZ-nearZ),  (-2*farZ*nearZ)/(farZ-nearZ),
          0.0,                  0.0,        -1.0,                          0.0));

     return camera_space_to_clip_space * cameraSpace;
}

vec4 project_standard_way(vec4 cameraSpace){

    float top = (-nearZ) * tan(fov * 3.14159265358979323846 / 360.0);
    float right = top * aspectRatio;

    mat4 proj =  mat4(
         nearZ / right, 0.0,         0.0,                               0.0,
         0.0,           nearZ / top, 0.0,                               0.0,
         0.0,           0.0,         -(farZ + nearZ) / (farZ - nearZ),  -2 * (farZ * nearZ) / (farZ - nearZ),
         0.0,           0.0,         -1.0,                              0.0);

     return transpose(proj)  * cameraSpace;
}


void main()
{
   // if you change the depth to be 1.0, and LEQUAL, instead of -1.0, and GREATER, and if
   // you change the nearZ farZ by negating them, then you could use the standard
   // projection matrix here:
   // gl_Position = project_standard_way(mvMatrix * vec4(position,1.0));
   gl_Position = project(mvMatrix * vec4(position,1.0));
   vs_out.color = vec4(color_in,1.0);
}
