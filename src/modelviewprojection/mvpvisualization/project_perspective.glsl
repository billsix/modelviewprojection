// project_perspective.glsl -- perspective projection animation (modelviewperspectiveprojection).
// time 90-95: squash x then y by near_z/z (the perspective-divide preview);
// 100-105: translate to the origin then scale to the NDC cube.
// (If you flip the depth convention to 1.0 / GL_LEQUAL and negate near_z/far_z,
//  a standard projection matrix could replace this.)
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

     return scale_to_ndc * translate_to_origin * scale_y * scale_x * cameraSpace;
}
