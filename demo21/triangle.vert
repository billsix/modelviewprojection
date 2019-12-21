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
