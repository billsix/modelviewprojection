// colorinvert.fs
//
// invert like a color negative

uniform sampler2D sampler0;

void main(void)
{
    vec4 sample = texture2D(sampler0, 
                            gl_TexCoord[0].st);

    // invert color components
    gl_FragColor.rgb = 1.0 - sample.rgb;
    gl_FragColor.a = 1.0;
}
