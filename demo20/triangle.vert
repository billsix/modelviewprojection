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
     //     nearZ)/cameraSpace.z, 0.0, 0.0, 0.0,
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
