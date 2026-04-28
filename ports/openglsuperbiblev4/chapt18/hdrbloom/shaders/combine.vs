// combine.vs
//
// Generic vertex transformation,
// pass through texture coordinate 

void main(void)
{ 
    // no transform
    gl_Position = gl_Vertex;

    // map object-space position onto unit sphere
    gl_TexCoord[0].st = gl_MultiTexCoord0.st;
}