// combine.fs
//
// take 4 incoming textures and
// tile them

uniform sampler2D sampler0;
uniform sampler2D sampler1;
uniform sampler2D sampler2;
uniform sampler2D sampler3;

void main(void)
{
    if (gl_TexCoord[0].s < 0.5)
    {
        if (gl_TexCoord[0].t < 0.5)
        {
            // bottom left
            gl_FragColor = texture2D(sampler0, gl_TexCoord[0].st);
        }
        else
        {
            // top left
            gl_FragColor = texture2D(sampler1, gl_TexCoord[0].st);
        }
    }
    else
    {
        if (gl_TexCoord[0].t < 0.5)
        {
            // bottom right
            gl_FragColor = texture2D(sampler2, gl_TexCoord[0].st);
        }
        else
        {
            // top right
            gl_FragColor = texture2D(sampler3, gl_TexCoord[0].st);
        }
    }
}
