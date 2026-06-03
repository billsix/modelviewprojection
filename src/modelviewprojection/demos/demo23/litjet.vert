// Copyright (c) 2018-2026 William Emerison Six
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

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal_in;

uniform mat4 mvpMatrix;
uniform mat4 modelMatrix;

out vec3 v_normal_ws;
out vec3 v_position_ws;

void main() {
    gl_Position = mvpMatrix * vec4(position, 1.0);

    // Specular needs the eye direction for each fragment, so we pass
    // the world-space position along with the normal.  Demo 22 only
    // needed Lambert (a normal-vs-light dot product) so it could skip
    // the position.
    vec4 ws = modelMatrix * vec4(position, 1.0);
    v_position_ws = ws.xyz;
    v_normal_ws = mat3(modelMatrix) * normal_in;
}
