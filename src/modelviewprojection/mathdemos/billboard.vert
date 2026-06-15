#version 330 core

// Camera-facing billboard for the cross-product demo's TeX labels.
//
// Each quad corner shares one world-space ``center``; ``offset`` is the corner's
// displacement in NDC (already aspect-/pixel-scaled by the CPU).  Projecting the
// center to clip space and then adding ``offset * clip.w`` makes the offset
// survive the perspective divide as a CONSTANT NDC (screen) size -- so the label
// stays the same on-screen size at any depth, and it works for the ortho views
// too (there clip.w == 1).
layout (location = 0) in vec3 center;
layout (location = 1) in vec2 offset;
layout (location = 2) in vec2 uv;

uniform mat4 vMatrix;
uniform mat4 pMatrix;

out vec2 v_uv;

void main()
{
    vec4 clip = pMatrix * vMatrix * vec4(center, 1.0);
    clip.xy += offset * clip.w;
    gl_Position = clip;
    v_uv = uv;
}
