// project_perspective.glsl -- perspective projection animation (modelviewperspectiveprojection).
// The four squash sub-steps -- squash x, squash y (the perspective-divide
// preview), translate to the origin, then scale to the NDC cube -- are driven by
// `squash_ratios` (x,y,z,w in [0,1]), one progress value per step.  These come
// from the timeline (Animation.gpu_progress), so there are NO hardcoded absolute
// times here: change a step's duration or add a step and the shader follows.
//
// squash x/y are GUARDED on ratio > 0: at ratio 0 they must be the identity, but
// they must NOT evaluate near_z/cameraSpace.z to get there -- that is inf*0 = NaN
// for z=0-plane geometry (the paddles, square, and axis arrow tips all sit at
// z=0 until the world->camera inverse moves them), and a NaN gl_Position silently
// drops the vertex, so the geometry vanishes until the inverse lifts it off z=0.
// (If you flip the depth convention to 1.0 / GL_LEQUAL and negate near_z/far_z,
//  a standard projection matrix could replace this.)
uniform vec4 squash_ratios;  // (squash x, squash y, translate, scale) progress

vec4 project(vec4 cameraSpace){

    float top = (-near_z) * tan(field_of_view * 3.14159265358979323846 / 360.0);
    float right = top * aspect_ratio;

    mat4 scale_x = mat4(1.0);
    if (squash_ratios.x > 0.0) {
        float xVal = 1.0 + (near_z/cameraSpace.z - 1.0) * squash_ratios.x;
        scale_x = transpose(mat4(
                                  xVal, 0.0, 0.0, 0.0,
                                  0.0,  1.0, 0.0, 0.0,
                                  0.0,  0.0, 1.0, 0.0,
                                  0.0,  0.0, 0.0, 1.0));
    }
    mat4 scale_y = mat4(1.0);
    if (squash_ratios.y > 0.0) {
        float yVal = 1.0 + (near_z/cameraSpace.z - 1.0) * squash_ratios.y;
        scale_y = transpose(mat4(
                                  1.0, 0.0,  0.0, 0.0,
                                  0.0, yVal, 0.0, 0.0,
                                  0.0, 0.0,  1.0, 0.0,
                                  0.0, 0.0,  0.0, 1.0));
    }
    // translate-to-origin has no vertex-z divide, so ratio 0 -> zVal 0 -> the
    // identity with no NaN risk; no guard needed.
    float zVal = (-((far_z + near_z) / 2.0)) * squash_ratios.z;
    mat4 translate_to_origin = transpose(mat4(
         1.0, 0.0, 0.0, 0.0,
         0.0, 1.0, 0.0, 0.0,
         0.0, 0.0, 1.0, zVal,
         0.0, 0.0, 0.0, 1.0));
    // scale-to-ndc divides only by right/top (finite, from near_z/fov), never by
    // a vertex coordinate, so it is also NaN-safe at ratio 0.
    float sxn = 1.0 + (1.0/right - 1.0) * squash_ratios.w;
    float syn = 1.0 + (1.0/top - 1.0) * squash_ratios.w;
    float szn = 1.0 + (2.0/(near_z - far_z) - 1.0) * squash_ratios.w;
    mat4 scale_to_ndc = transpose(mat4(
         sxn,  0.0,  0.0,  0.0,
         0.0,  syn,  0.0,  0.0,
         0.0,  0.0,  szn,  0.0,
         0.0,  0.0,  0.0,  1.0));

    //use transpose to put the matrix in column major order
     return scale_to_ndc * translate_to_origin * scale_y * scale_x * cameraSpace;
}
