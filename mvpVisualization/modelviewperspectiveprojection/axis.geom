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

mat4 ndc_to_screen(){
     mat4 translate = transpose(mat4(
                                  1.0, 0.0,  0.0, u_viewport_size.x / 2.0,
                                  0.0, 1.0 , 0.0, u_viewport_size.y / 2.0,
                                  0.0, 0.0,  1.0, 0.0,
                                  0.0, 0.0,  0.0, 1.0));
     mat4 scale = transpose(mat4(
                                  u_viewport_size.x / 2.0, 0.0,                     0.0, 0.0,
                                  0.0,                     u_viewport_size.y / 2.0, 0.0, 0.0,
                                  0.0,                     0.0,                     1.0, 0.0,
                                  0.0,                     0.0,                     0.0, 1.0));
     return translate * scale;
}

void main(){
     vec4 p1_clip = gl_in[0].gl_Position;
     vec4 p2_clip = gl_in[1].gl_Position;

     fColor = gs_in[0].color;

     vec4 p1_ndc = vec4(p1_clip.xyz / p1_clip.w, 1.0);
     vec4 p2_ndc = vec4(p2_clip.xyz / p2_clip.w, 1.0);

     mat4 matrix_ndc_to_screen = ndc_to_screen();

     vec4 p1_screen = matrix_ndc_to_screen * p1_ndc;
     vec4 p2_screen = matrix_ndc_to_screen * p2_ndc;

     vec4 unit_direction_of_line_screen = normalize(p2_screen - p1_screen);
     vec4 thickness_orthogonal_direction_of_line_screen = vec4(u_thickness * vec2(-unit_direction_of_line_screen.y,
                                                                                  unit_direction_of_line_screen.x),
                                                               unit_direction_of_line_screen.z,
                                                               0.0);

     vec4 unit_orthogonal_direction_of_line_ndc = transpose(inverse(matrix_ndc_to_screen)) *
       thickness_orthogonal_direction_of_line_screen;

     vec2 p1_unit_orthogonal_direction_of_line_clip = (unit_orthogonal_direction_of_line_ndc * p1_clip.w).xy;
     vec2 p2_unit_orthogonal_direction_of_line_clip = (unit_orthogonal_direction_of_line_ndc * p2_clip.w).xy;


     gl_Position = p1_clip + vec4(p1_unit_orthogonal_direction_of_line_clip,
                                  0.0,
                                  0.0);
     EmitVertex();
     gl_Position = p1_clip - vec4(p1_unit_orthogonal_direction_of_line_clip,
                                  0.0,
                                  0.0);
     EmitVertex();
     gl_Position = p2_clip + vec4(p2_unit_orthogonal_direction_of_line_clip,
                                  0.0,
                                  0.0);
     EmitVertex();
     gl_Position = p2_clip - vec4(p2_unit_orthogonal_direction_of_line_clip,
                                  0.0,
                                  0.0);
     EmitVertex();
     EndPrimitive();

}
