// Copyright (c) 2018-2025 William Emerison Six
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place - Suite 330,
// Boston, MA 02111-1307, USA.


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

mat4 inverseTranspose(mat4 mat) {
    mat3 upper3x3 = mat3(mat);
    mat3 inverseTransposeUpper3x3 = transpose(inverse(upper3x3));
    vec3 negatedFourthColumn = -mat[3].xyz;

    return mat4(
        vec4(inverseTransposeUpper3x3[0], 0.0),
        vec4(inverseTransposeUpper3x3[1], 0.0),
        vec4(inverseTransposeUpper3x3[2], 0.0),
        vec4(negatedFourthColumn, 1.0)
    );
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



     vec4 unit_orthogonal_direction_of_line_ndc = inverseTranspose(matrix_ndc_to_screen) *
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
