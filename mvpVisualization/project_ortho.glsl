// project_ortho.glsl -- orthographic projection animation (modelvieworthoprojection).
// time 90-95: translate the view volume to the origin; 95-100: scale to NDC.
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

     return scale_to_ndc * translate_to_origin * cameraSpace;
}
