//Copyright (c) 2023 William Emerison Six
//
//Permission is hereby granted, free of charge, to any person obtaining a copy
//of this software and associated documentation files (the "Software"), to deal
//in the Software without restriction, including without limitation the rights
//to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//copies of the Software, and to permit persons to whom the Software is
//furnished to do so, subject to the following conditions:
//
//The above copyright notice and this permission notice shall be included in all
//copies or substantial portions of the Software.
//
//THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//SOFTWARE.


#version 330 core

layout (lines) in;
layout (triangle_strip, max_vertices = 4) out;

uniform vec2 u_viewport_size;
uniform float u_thickness;

in VS_OUT {
  vec4 color;
} gs_in[];


out vec4 fColor;

void main(){
     vec4 p1 = gl_in[0].gl_Position;
     vec4 p2 = gl_in[1].gl_Position;

     fColor = gs_in[0].color;
     vec2 dir = normalize((p2.xy / p2.w - p1.xy/p1.w) * u_viewport_size);
     vec2 offset = vec2(-dir.y, dir.x) * u_thickness / u_viewport_size;

     gl_Position = p1 + vec4(offset.xy * p1.w, 0.0, 0.0);
     EmitVertex();
     gl_Position = p1 - vec4(offset.xy * p1.w, 0.0, 0.0);
     EmitVertex();
     gl_Position = p2 + vec4(offset.xy * p2.w, 0.0, 0.0);
     EmitVertex();
     gl_Position = p2 - vec4(offset.xy * p2.w, 0.0, 0.0);
     EmitVertex();
     EndPrimitive();

}