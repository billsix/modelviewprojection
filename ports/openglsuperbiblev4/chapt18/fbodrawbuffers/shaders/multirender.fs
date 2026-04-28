// multirender.fs
//
// 4 different outputs!

uniform sampler2D sampler0;
uniform vec2 tc_offset[9];

void main(void)
{
    vec4 sample[9];

    // enhance the blur by adding an LOD bias
    for (int i = 0; i < 9; i++)
    {
        sample[i] = texture2D(sampler0, 
                              gl_TexCoord[0].st + (tc_offset[i] * 3.0), 3.0);
    }

    // output 0 is a blur
    gl_FragData[0] = (sample[0] + (2.0*sample[1]) + sample[2] + 
                    (2.0*sample[3]) + (2.0*sample[5]) + 
                    sample[6] + (2.0*sample[7]) + sample[8]) / 12.0;

    // now grab the unbiased samples again
    for (int i = 0; i < 9; i++)
    {
        sample[i] = texture2D(sampler0, 
                              gl_TexCoord[0].st + tc_offset[i]);
    }

    // output 1 is a Laplacian edge-detect
    gl_FragData[1] = (sample[4] * 8.0) - 
                    (sample[0] + sample[1] + sample[2] + 
                     sample[3] + sample[5] + 
                     sample[6] + sample[7] + sample[8]);

    // output 2 is grayscale
    gl_FragData[2] = vec4(vec3(dot(sample[4].rgb, vec3(0.3, 0.59, 0.11))), 1.0);

    // output 3 is an inverse
    gl_FragData[3] = vec4(vec3(1.0) - sample[4].rgb, 1.0);
}
