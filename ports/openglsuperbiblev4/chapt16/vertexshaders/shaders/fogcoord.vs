// fogcoord.vs
//
// Generic vertex transformation,
// diffuse and specular lighting,
// per-vertex fogcoord

uniform vec3 lightPos[1];

void main(void)
{
    // normal MVP transform
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

    vec3 N = normalize(gl_NormalMatrix * gl_Normal);
    vec4 V = gl_ModelViewMatrix * gl_Vertex;
    vec3 L = normalize(lightPos[0] - V.xyz);
    vec3 H = normalize(L + vec3(0.0, 0.0, 1.0));
    const float specularExp = 128.0;

    // calculate diffuse lighting
    float NdotL = max(0.0, dot(N, L));
    vec4 diffuse = gl_Color * vec4(NdotL);

    // calculate specular lighting
    float NdotH = max(0.0, dot(N, H));
    vec4 specular = vec4(0.0);
    if (NdotL > 0.0)
        specular = vec4(pow(NdotH, specularExp));

    // calculate fog coordinate: distance from eye
    gl_FogFragCoord = length(V);

    // sum the diffuse and specular components
    gl_FrontColor = diffuse + specular;
}
