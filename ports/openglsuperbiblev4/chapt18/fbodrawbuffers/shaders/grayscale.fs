// grayscale.fs
//
// convert RGB to grayscale

uniform sampler2D sampler0;

void main(void)
{
    vec4 sample = texture2D(sampler0, 
                            gl_TexCoord[0].st);

    // Convert to grayscale
    float gray = dot(sample.rgb, vec3(0.3, 0.59, 0.11));

    // replicate grayscale to RGB components
    gl_FragColor = vec4(gray, gray, gray, 1.0);
}
