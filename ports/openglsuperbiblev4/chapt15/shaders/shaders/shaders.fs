// Hello World fragment shader. Mixes primary and secondary color
// 50/50 then multiplies by a flicker factor uniform.

uniform float flickerFactor;

void main(void)
{
    // Mix primary and secondary colors, 50/50
    vec4 temp = mix(gl_Color, vec4(vec3(gl_SecondaryColor), 1.0), 0.5);

    // Multiply by flicker factor
    gl_FragColor = temp * flickerFactor;
}
