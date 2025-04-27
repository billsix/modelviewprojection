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

layout (location = 0) in vec3 position;

uniform mat4 mMatrix;
uniform mat4 vMatrix;
uniform mat4 pMatrix;
uniform vec3 color;

out VS_OUT {
  vec4 color;
} vs_out;

void main()
{
  gl_Position = pMatrix * vMatrix * mMatrix * vec4(position,1.0);
  vs_out.color = vec4(color,1.0);
}
