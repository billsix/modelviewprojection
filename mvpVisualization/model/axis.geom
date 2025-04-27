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