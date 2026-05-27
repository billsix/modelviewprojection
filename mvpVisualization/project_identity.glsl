// project_identity.glsl -- appended to a shared .vert for STATIC pipelines.
// No projection animation: model / view / projection are applied directly by
// the .vert's main(), so project() is the identity on camera space.
vec4 project(vec4 cameraSpace)
{
    return cameraSpace;
}
