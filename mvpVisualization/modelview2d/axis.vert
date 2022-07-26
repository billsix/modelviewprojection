//Copyright (c) 2018-2022 William Emerison Six
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

uniform mat4 mMatrix;
uniform mat4 vMatrix;
uniform mat4 pMatrix;
uniform float fov;
uniform float aspectRatio;
uniform float nearZ;
uniform float farZ;
uniform vec3 color;
uniform float time;

out VS_OUT {
  vec4 color;
} vs_out;

vec4 project(vec4 cameraSpace){

    float top = (-nearZ) * tan(fov * 3.14159265358979323846 / 360.0);
    float right = top * aspectRatio;

    float scaleXRatio = max(1.0, (time - 90.0)/5.0);
    float scaleYRatio = max(1.0, (time - 95.0)/5.0);
    float traslate_to_originRatio = max(1.0, (time - 100.0)/5.0);
    float scaleToNDCRatio = max(1.0, (time - 105.0)/5.0);

    mat4 scale_x = transpose(mat4(
                                  nearZ/cameraSpace.z, 0.0, 0.0, 0.0,
                                  0.0,                 1.0, 0.0, 0.0,
                                  0.0,                 0.0, 1.0, 0.0,
                                  0.0,                 0.0, 0.0, 1.0));
    mat4 scale_y = transpose(mat4(
                                  1.0, 0.0,                 0.0, 0.0,
                                  0.0, nearZ/cameraSpace.z, 0.0, 0.0,
                                  0.0, 0.0,                 1.0, 0.0,
                                  0.0, 0.0,                 0.0, 1.0));
    mat4 translate_to_origin = transpose(mat4(
         1.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 0.0, 0.0,
         0.0, 0.0, 1.0, -((farZ + nearZ) / 2.0),
         0.0, 0.0, 0.0, 1.0));
    mat4 scale_to_ndc = transpose(mat4(
         1.0/right,     0.0,           0.0,                  0.0,
         0.0,           1.0/top,       0.0,                  0.0,
         0.0,           0.0,           2.0/(nearZ - farZ),   0.0,
         0.0,           0.0,           0.0,                  1.0));

    //use transpose to put the matrix in column major order
    if (time < 90){
      scale_x = mat4(1.0);
    }
    if (time < 95){
      scale_y =  mat4(1.0);
    }
    if (time < 100){
      translate_to_origin = mat4(1.0);
    }
    if (time < 105){
      scale_to_ndc =  mat4(1.0);
    }

//ortho


     return scale_to_ndc * translate_to_origin * scale_y * scale_x * cameraSpace;
}


void main()
{
  gl_Position = pMatrix * vMatrix * project(mMatrix * vec4(position,1.0));
   vs_out.color = vec4(color,1.0);
}
