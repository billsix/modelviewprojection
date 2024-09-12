//Copyright (c) 2018-2024 William Emerison Six
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

    float translateRatio = min((time - 90.0)/5.0, 1.0);
    mat4 translate_to_origin = transpose(mat4(
         1.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 0.0, 0.0,
         0.0, 0.0, 1.0, 16.0/2 * translateRatio,
         0.0, 0.0, 0.0, 1.0));
    float scaleRatio = min((time - 95.0)/5.0, 1.0);
    float xVal = 1.0 + (1.0/5.0 - 1.0) * scaleRatio;
    float yVal = 1.0 + (1.0/5.0 - 1.0) * scaleRatio;
    float zVal = 1.0 + (2.0/15.0 - 1) * scaleRatio;
    mat4 scale_to_ndc = transpose(mat4(
         xVal,     0.0,     0.0,    0.0,
         0.0,      yVal,    0.0,    0.0,
         0.0,      0.0,     zVal,   0.0,
         0.0,      0.0,     0.0,    1.0));

    //use transpose to put the matrix in column major order
    if (time < 90){
      translate_to_origin = mat4(1.0);
    }
    if (time < 95){
      scale_to_ndc =  mat4(1.0);
    }

//ortho


     return scale_to_ndc * translate_to_origin * cameraSpace;
}


void main()
{
  gl_Position = pMatrix * vMatrix * project(mMatrix * vec4(position,1.0));
   vs_out.color = vec4(color,1.0);
}
