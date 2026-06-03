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

// Universal fragment shader: pass the interpolated vertex colour through.
// Used by every pipeline whose vertex shader emits the VS_OUT.color block
// (per_vertex_color.vert and uniform_color.vert).  The geometry-shader path
// uses passthrough_geom.frag instead.

out vec4 color;

in VS_OUT {
  vec4 color;
} fs_in;

void main()
{
   color = fs_in.color;
}
