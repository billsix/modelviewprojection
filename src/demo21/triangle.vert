//Copyright (c) 2018-2020 William Emerison Six
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

     //// use transpose to put the matrix in column major order
     //mat4 scale_x = transpose(mat4(
     //     nearZ/cameraSpace.z, 0.0, 0.0, 0.0,
     //     0.0,                  1.0, 0.0, 0.0,
     //     0.0,                  0.0, 1.0, 0.0,
     //     0.0,                  0.0, 0.0, 1.0));
     //mat4 scale_y = transpose(mat4(
     //     1.0, 0.0,                 0.0, 0.0,
     //     0.0, nearZ/cameraSpace.z, 0.0, 0.0,
     //     0.0, 0.0,                 1.0, 0.0,
     //     0.0, 0.0,                 0.0, 1.0));

    // ortho
    //mat4 translate_to_origin = transpose(mat4(
    //      1.0, 0.0, 0.0, 0.0,
    //      0.0, 1.0, 0.0, 0.0,
    //      0.0, 0.0, 1.0, -((farZ + nearZ) / 2.0),
    //      0.0, 0.0, 0.0, 1.0));
    // mat4 scale_to_ndc = transpose(mat4(
    //      1.0/right,     0.0,           0.0,                  0.0,
    //      0.0,           1.0/top,       0.0,                  0.0,
    //      0.0,           0.0,           2.0/(nearZ - farZ),   0.0,
    //      0.0,           0.0,           0.0,                  1.0));

    //scale_y * scale_x =
    //      nearZ/cameraSpace.z, 0.0,                 0.0, 0.0,
    //      0.0,                 nearZ/cameraSpace.z, 0.0, 0.0,
    //      0.0,                 0.0,                 1.0, 0.0,
    //      0.0,                 0.0,                 0.0, 1.0))
    // translate_to_origin * scale_y * scale_x =
    //      nearZ/cameraSpace.z, 0.0,                 0.0, 0.0,
    //      0.0,                 nearZ/cameraSpace.z, 0.0, 0.0,
    //      0.0,                 0.0,                 1.0, -((farZ + nearZ) / 2.0),
    //      0.0,                 0.0,                 0.0, 1.0))
    // scale_to_ndc * translate_to_origin * scale_y * scale_x =
    //      nearZ/(right * cameraSpace.z), 0.0,                       0.0,                0.0,
    //      0.0,                           nearZ/(top*cameraSpace.z), 0.0,                0.0,
    //      0.0,                           0.0,                       2.0/(nearZ - farZ), 2.0/(nearZ - farZ) * -((farZ + nearZ) / 2.0),
    //      0.0,                           0.0,                       0.0,                1.0))
    // scale_to_ndc * translate_to_origin * scale_y * scale_x =
    //      nearZ/(right * cameraSpace.z), 0.0,                       0.0,                0.0,
    //      0.0,                           nearZ/(top*cameraSpace.z), 0.0,                0.0,
    //      0.0,                           0.0,                       2.0/(nearZ - farZ), -(farZ + nearZ)/(nearZ - farZ),
    //      0.0,                           0.0,                       0.0,                1.0))

     mat4 camera_space_to_ndc_space = transpose(mat4(
          nearZ/(right * cameraSpace.z), 0.0,                       0.0,                0.0,
          0.0,                           nearZ/(top*cameraSpace.z), 0.0,                0.0,
          0.0,                           0.0,                       2.0/(nearZ - farZ), -(farZ + nearZ)/(nearZ - farZ),
          0.0,                           0.0,                       0.0,                1.0));


     return camera_space_to_ndc_space * cameraSpace;
}


void main()
{
   gl_Position = project(mvMatrix * vec4(position,1.0));
   vs_out.color = vec4(color_in,1.0);
}
