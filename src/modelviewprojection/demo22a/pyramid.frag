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

in vec3 v_normal_ws;
in vec2 v_texcoord;

uniform sampler2D tex;
uniform vec3 flatColor;          // used when useTexture is false
uniform bool useTexture;
uniform bool useLighting;
uniform vec3 lightDirWS;         // direction *toward* the light, world-space
uniform vec3 ambientColor;
uniform vec3 diffuseColor;

out vec4 fragColor;

void main() {
    vec3 base = useTexture ? texture(tex, v_texcoord).rgb : flatColor;

    if (useLighting) {
        vec3 n = normalize(v_normal_ws);
        float diff = max(dot(n, normalize(lightDirWS)), 0.0);
        vec3 lit = ambientColor * base + diffuseColor * base * diff;
        fragColor = vec4(lit, 1.0);
    } else {
        fragColor = vec4(base, 1.0);
    }
}
