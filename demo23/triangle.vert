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
    // (1) nearZ and farZ have been made positive in the Python code
    // (2) the Default depth in the python code is 1.0, and the depth buffer tests <= the current depth.
    //    therefore, we need to reflect over the Z axis.  Why is this done?  I don't know the reason
    //    but it works either way

    // For (1)

    //float top = (-nearZ) * tan(fov * 3.14159265358979323846 / 360.0);
    //float right = top * aspectRatio;

    // mat4 camera_space_to_clip_space = transpose(mat4(
    //      -nearZ/right,         0.0,        0.0,                           0.0,
    //      0.0,                  -nearZ/top, 0.0,                           0.0,
    //      0.0,                  0.0,        (farZ + nearZ)/(farZ-nearZ),  (-2*farZ*nearZ)/(farZ-nearZ),
    //      0.0,                  0.0,        -1.0,                          0.0));

    // return camera_space_to_clip_space * cameraSpace;

    float top = nearZ * tan(fov * 3.14159265358979323846 / 360.0);
    float right = top * aspectRatio;

    // mat4 camera_space_to_clip_space = transpose(mat4(
    //      --nearZ/right,         0.0,        0.0,                           0.0,
    //      0.0,                  --nearZ/top, 0.0,                           0.0,
    //      0.0,                  0.0,        (-farZ + -nearZ)/(-farZ--nearZ),  (-2*-farZ*-nearZ)/(-farZ--nearZ),
    //      0.0,                  0.0,        -1.0,                          0.0));
     mat4 camera_space_to_clip_space1 = transpose(mat4(
          nearZ/right,         0.0,       0.0,                           0.0,
          0.0,                 nearZ/top, 0.0,                           0.0,
          0.0,                 0.0,       -(farZ + nearZ)/(-farZ+nearZ), (-2*farZ*nearZ)/(-farZ+nearZ),
          0.0,                 0.0,       -1.0,                          0.0));

    // End (1)
    // For (2)
     mat4 reflect_z = transpose(mat4(
          1.0,  0.0, 0.0,  0.0,
          0.0,  1.0, 0.0,  0.0,
          0.0,  0.0, -1.0, 0.0,
          0.0,  0.0, 0.0,  1.0));

     // camera_space_to_clip_space2 = reflect_z * camera_space_to_clip_space1
     mat4 camera_space_to_clip_space2 = transpose(mat4(
          nearZ/right,         0.0,       0.0,                           0.0,
          0.0,                 nearZ/top, 0.0,                           0.0,
          0.0,                 0.0,       -(farZ + nearZ)/(farZ-nearZ), (-2*farZ*nearZ)/(farZ-nearZ),
          0.0,                 0.0,       -1.0,                          0.0));
    // End (2)

     return camera_space_to_clip_space2 * cameraSpace;

}

vec4 project_standard_way(vec4 cameraSpace){

    // now that nearZ is a positive value, no need to negate it
    float top = nearZ * tan(fov * 3.14159265358979323846 / 360.0);
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
