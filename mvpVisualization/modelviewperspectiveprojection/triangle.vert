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
layout (location = 1) in vec3 color_in;

uniform mat4 mMatrix;
uniform mat4 vMatrix;
uniform mat4 pMatrix;
uniform float field_of_view;
uniform float aspect_ratio;
uniform float near_z;
uniform float far_z;
uniform float time;

out VS_OUT {
  vec4 color;
} vs_out;

vec4 project(vec4 cameraSpace){

    float top = (-near_z) * tan(field_of_view * 3.14159265358979323846 / 360.0);
    float right = top * aspect_ratio;

    float scaleXRatio = min((time - 90.0)/5.0, 1.0);
    float xVal = 1 + (near_z/cameraSpace.z - 1) * scaleXRatio;

    mat4 scale_x = transpose(mat4(
                                  xVal, 0.0, 0.0, 0.0,
                                  0.0,                 1.0, 0.0, 0.0,
                                  0.0,                 0.0, 1.0, 0.0,
                                  0.0,                 0.0, 0.0, 1.0));
    float scaleYRatio = min((time - 95.0)/5.0, 1.0);
    float yVal = 1 + (near_z/cameraSpace.z - 1) * scaleYRatio;
    mat4 scale_y = transpose(mat4(
                                  1.0, 0.0,                 0.0, 0.0,
                                  0.0, yVal, 0.0, 0.0,
                                  0.0, 0.0,                 1.0, 0.0,
                                  0.0, 0.0,                 0.0, 1.0));
    float translateRatio = min((time - 100.0)/5.0, 1.0);
    float zVal = (-((far_z + near_z) / 2.0)) * translateRatio;
    mat4 translate_to_origin = transpose(mat4(
         1.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 0.0, 0.0,
         0.0, 0.0, 1.0, zVal,
         0.0, 0.0, 0.0, 1.0));
    float scaleRatio = min((time - 105.0)/5.0, 1.0);
    xVal = 1.0 + (1.0/right - 1.0) * scaleRatio;
    yVal = 1.0 + (1.0/top - 1.0) * scaleRatio;
    zVal = 1.0 + (2.0/(near_z - far_z) - 1) * scaleRatio;
    mat4 scale_to_ndc = transpose(mat4(
         xVal,     0.0,     0.0,    0.0,
         0.0,      yVal,    0.0,    0.0,
         0.0,      0.0,     zVal,   0.0,
         0.0,      0.0,     0.0,    1.0));

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
  // mMatrix has the "virtual camera's" view transformations in it.
  // so, from right to left, model, view (virtual, moving camera), project, view (our view), project (our view)
  gl_Position = pMatrix * vMatrix * project(mMatrix * vec4(position,1.0));
   vs_out.color = vec4(color_in,1.0);
}
