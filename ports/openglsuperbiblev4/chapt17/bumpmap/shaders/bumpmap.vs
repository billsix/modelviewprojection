// bumpmap.vs
//
// setup interpolants for bumpmap lighting

uniform vec3 lightPos0;
varying vec3 L;

void main(void)
{
    // normal MVP transform
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

    // bumpmap texcoords
    gl_TexCoord[0].xy = gl_MultiTexCoord0.xy;

    // put tangent-space light vector into texcoord 1
    vec3 Lobj = lightPos0 - gl_Vertex.xyz;
    L.x = dot(Lobj, gl_MultiTexCoord1.xyz); // tangent
    L.y = dot(Lobj, gl_MultiTexCoord2.xyz); // binormal
    L.z = dot(Lobj, gl_MultiTexCoord3.xyz); // normal

    // Copy the primary color
    gl_FrontColor = gl_Color;
}
