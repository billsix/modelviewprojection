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

    float top = abs(nearZ) * tan(fov * 3.14159265358979323846 / 360.0);
    float right = top * aspectRatio;

     // use transpose to put the matrix in column major order
     // cameraSpace visible range for .x [-right/(abs(nearZ)/abs(cameraSpace.z)), (right/abs(nearZ)/abs(cameraSpace.z))]
     // cameraSpace visible range for .y [-top/(abs(nearZ)/abs(cameraSpace.z)), top/(abs(nearZ)/abs(cameraSpace.z))]
     // cameraSpace visible range for .z [near,far]

     mat4 scale_x = transpose(mat4(
          abs(nearZ)/abs(cameraSpace.z), 0.0, 0.0, 0.0,
          0.0,                           1.0, 0.0, 0.0,
          0.0,                           0.0, 1.0, 0.0,
          0.0,                           0.0, 0.0, 1.0));
     // scale_x visible range for .x [-right, right]
     // scale_x visible range for .y [-top/(abs(nearZ)/abs(cameraSpace.z)), top/(abs(nearZ)/abs(cameraSpace.z))]
     // scale_z visible range for .z [near,far]
     mat4 scale_y = transpose(mat4(
          1.0, 0.0,                            0.0, 0.0,
          0.0, abs(nearZ)/abs(cameraSpace.z),  0.0, 0.0,
          0.0, 0.0,                            1.0, 0.0,
          0.0, 0.0,                            0.0, 1.0));
     // scale_y visible range for .x [-right,right]
     // scale_y visible range for .y [-top,top]
     // scale_y visible range for .z [near,far]


    float x_length = right * 2;
    float y_length = top * 2;
    float z_length = farZ - nearZ;

    float midpoint_x = 0.0 ; // centered on x
    float midpoint_y = 0.0 ; // centered on y
    float midpoint_z = (farZ + nearZ) / 2.0;

    // ortho
    //mat4 translate_to_origin = transpose(mat4(
    //      1.0, 0.0, 0.0, -midpoint_x,
    //      0.0, 1.0, 0.0, -midpoint_y,
    //      0.0, 0.0, 1.0, -midpoint_z,
    //      0.0, 0.0, 0.0, 1.0));
    // mat4 scale_to_ndc = transpose(mat4(
    //      2.0/x_length,  0.0,           0.0,             0.0,
    //      0.0,           2.0/y_length,  0.0,             0.0,
    //      0.0,           0.0,           2.0/-z_length,   0.0,
    //      0.0,           0.0,           0.0,             1.0));

    // since midpoint_x and midpoint_y = 0, substitute those in

    // ortho
    mat4 translate_to_origin = transpose(mat4(
          1.0, 0.0, 0.0, 0.0,
          0.0, 1.0, 0.0, 0.0,
          0.0, 0.0, 1.0, -((farZ + nearZ) / 2.0),
          0.0, 0.0, 0.0, 1.0));
     // translate_to_origin visible range for .x [-right,right]
     // translate_to_origin visible range for .y [-top,top]
     // translate_to_origin visible range for .z [-(nearZ-farZ)/2,(nearZ-farZ)/2]

     // since x_length = 2* right, and y_length = 2*top, substitute those in
     mat4 scale_to_ndc = transpose(mat4(
         1.0/right,     0.0,           0.0,                  0.0,
         0.0,           1.0/top,       0.0,                  0.0,
         0.0,           0.0,           2.0/(nearZ - farZ),   0.0,
         0.0,           0.0,           0.0,                  1.0));
     // scale_to_ndc visible range for .x [-1.0,1.0]
     // scale_to_ndc visible range for .y [-1.0,1.0]
     // scale_to_ndc visible range for .z [-1.0,1.0]

     return (scale_to_ndc * translate_to_origin  * scale_y * scale_x) * cameraSpace;
}

vec4 project_standard_way(vec4 cameraSpace){

    float top = abs(nearZ) * tan(fov * 3.14159265358979323846 / 360.0);
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
