// project_modelview2d.glsl -- 2D orthographic squash (modelview2d demo).
// At time >= 65 the world's x/y scale interpolates to the 1/10 NDC scale.
vec4 project(vec4 cameraSpace){

    float scaleRatio = min((time - 65.0)/5.0, 1.0);
    float xVal = 1.0 + (1.0/10.0 - 1.0) * scaleRatio;
    float yVal = 1.0 + (1.0/10.0 - 1.0) * scaleRatio;
    mat4 scale_to_ndc = transpose(mat4(
         xVal,     0.0,     0.0,    0.0,
         0.0,      yVal,    0.0,    0.0,
         0.0,      0.0,     1.0,   0.0,
         0.0,      0.0,     0.0,    1.0));

    if (time < 65){
      scale_to_ndc =  mat4(1.0);
    }

     return scale_to_ndc * cameraSpace;
}
