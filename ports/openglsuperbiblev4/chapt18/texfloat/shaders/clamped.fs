// clamped.fs
//
// No tone mapping: clamp [0,oo) -> [0,1]

uniform sampler2D sampler0;

void main(void)
{
    vec4 sample = texture2D(sampler0, 
                            gl_TexCoord[0].st);

    // invert color components
    gl_FragColor.rgb = clamp(sample.rgb, 0.0, 1.0);
    gl_FragColor.a = 1.0;
}
