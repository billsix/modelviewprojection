// show2d.vs
//
// Generic vertex transformation,
// pass through texture coordinate 

void main(void)
{ 
    // no transform
    gl_Position = gl_Vertex;

    // pass through texcoord
    gl_TexCoord[0].st = gl_MultiTexCoord0.st;
}