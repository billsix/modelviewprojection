// trival.fs
//
// Trivial tone mapping: map [0,oo) -> [0,1)

uniform sampler2D sampler0;

void main(void)
{
    vec4 sample = texture2D(sampler0, 
                            gl_TexCoord[0].st);

    // invert color components
    gl_FragColor.rgb = sample.rgb / (sample.rgb + 1.0);
    gl_FragColor.a = 1.0;
}
