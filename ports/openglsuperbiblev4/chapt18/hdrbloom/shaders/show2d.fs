// show2d.fs
//
// just spit out the 2D texture

uniform sampler2D sampler0;

void main(void)
{
    gl_FragColor = texture2D(sampler0, gl_TexCoord[0].st);
}
