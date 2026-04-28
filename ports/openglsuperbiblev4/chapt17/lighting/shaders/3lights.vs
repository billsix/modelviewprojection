// 3lights.vs
//
// set up interpolants for 3 specular lights

uniform vec3 lightPos[3];
varying vec3 N, L[3];

void main(void)
{
    // vertex MVP transform
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

    vec4 V = gl_ModelViewMatrix * gl_Vertex;

    // eye-space normal
    N = gl_NormalMatrix * gl_Normal;

    // Light vectors
    for (int i = 0; i < 3; i++)
        L[i] = lightPos[i] - V.xyz;

    // Copy the primary color
    gl_FrontColor = gl_Color;
}
