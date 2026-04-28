// sepspec.vs
//
// Generic vertex transformation,
// diffuse and specular lighting
// interpolated separately

uniform vec3 lightPos[1];

void main(void)
{
    // normal MVP transform
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

    vec3 N = normalize(gl_NormalMatrix * gl_Normal);
    vec4 V = gl_ModelViewMatrix * gl_Vertex;
    vec3 L = normalize(lightPos[0] - V.xyz);
    vec3 H = normalize(L  + normalize(-V.xyz));
    const float specularExp = 128.0;

    // put diffuse into primary color
    float NdotL = max(0.0, dot(N, L));
    gl_FrontColor = gl_Color * vec4(NdotL);

    // put specular into secondary color
    float NdotH = max(0.0, dot(N, H));
    gl_FrontSecondaryColor = (NdotL > 0.0) ?
                             vec4(pow(NdotH, specularExp)) :
                             vec4(0.0);
}
