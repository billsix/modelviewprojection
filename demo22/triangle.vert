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

    // put into clipspace, not ndc.
    // clip space to ndc, given [x_clip,y_clip,z_clip,w_clip] =
    // [x_clip/w_clip,y_clip/w_clip,z_clip/w_clip,w_clip/w_clip]

    // to ensure that we don't have to make a new projection matrix for each
    // vertex, make the w_clip be the cameraSpace's z


    // because cameraSpace's z coordinate is negative, we want to scale
    // all dimensions without flipping, hence the negative sign
    // in front of cameraSpace.z
     mat4 ndc_space_to_clip_space = transpose(mat4(
          (-cameraSpace.z), 0.0,              0.0,              0.0,
          0.0,              (-cameraSpace.z), 0.0,              0.0,
          0.0,              0.0,              (-cameraSpace.z), 0.0,
          0.0,              0.0,              0.0,              (-cameraSpace.z)));


     mat4 camera_space_to_ndc_space = transpose(mat4(
          nearZ/(right * cameraSpace.z), 0.0,                       0.0,                0.0,
          0.0,                           nearZ/(top*cameraSpace.z), 0.0,                0.0,
          0.0,                           0.0,                       2.0/(nearZ - farZ), -(farZ + nearZ)/(nearZ - farZ),
          0.0,                           0.0,                       0.0,                1.0));

     // camera_space_to_clip_space = ndc_space_to_clip_space * camera_space_to_ndc_space
     mat4 camera_space_to_clip_space = transpose(mat4(
          -nearZ/right,         0.0,        0.0,                                   0.0,
          0.0,                  -nearZ/top, 0.0,                                   0.0,
          0.0,                  0.0,        2.0*(-cameraSpace.z)/(nearZ - farZ),   (-cameraSpace.z)*(-(farZ + nearZ)/(nearZ - farZ)),
          0.0,                  0.0,        0.0,                                   -cameraSpace.z));


     // z_ndc(cameraSpace) = (cameraSpace.z * (2.0*(-cameraSpace.z)/(nearZ - farZ)) +   (-cameraSpace.z)*(-(farZ + nearZ)/(nearZ - farZ)))/cameraSpace.z
     // z_ndc(cameraSpace) = (2.0*(-cameraSpace.z)/(nearZ - farZ)) +   ((farZ + nearZ)/(nearZ - farZ))
     // z_ndc(nearZ) = (2.0*(-nearZ)/(nearZ - farZ)) +   ((farZ + nearZ)/(nearZ - farZ))
     // z_ndc(nearZ) = (2.0*(-nearZ) + (farZ + nearZ))/(nearZ - farZ)
     // z_ndc(nearZ) = (2.0*(-nearZ) + (farZ + nearZ))/(nearZ - farZ)
     // z_ndc(nearZ) = (farZ - nearZ))/(nearZ - farZ)
     // z_ndc(nearZ) = (farZ - nearZ))/(nearZ - farZ)
     // z_ndc(nearZ) = -1.0


     // z_ndc(farZ) = (2.0*(-farZ)/(nearZ - farZ)) +   ((farZ + nearZ)/(nearZ - farZ))
     // z_ndc(farZ) = ((2.0*(-farZ) + (farZ + nearZ))/(nearZ - farZ))
     // z_ndc(farZ) = ( nearZ - farZ)/(nearZ - farZ))
     // z_ndc(farZ) = 1.0

     // modelspace to ndc, then ndc back to clip space, which the hardware turns back into NDC
     //        return ndc_space_to_clip_space * camera_space_to_ndc_space * cameraSpace;
     return camera_space_to_clip_space * cameraSpace;
}


void main()
{
   gl_Position = project(mvMatrix * vec4(position,1.0));
   vs_out.color = vec4(color_in,1.0);
}
