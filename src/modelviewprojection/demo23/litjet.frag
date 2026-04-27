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
in vec3 v_position_ws;

uniform vec3 baseColor;
uniform vec3 cameraPosWS;
uniform vec3 lightDirWS;       // direction *toward* the light, normalized
uniform vec3 ambientColor;
uniform vec3 diffuseColor;
uniform vec3 specularColor;
uniform float shininess;
uniform int  lightingMode;     // 0 unlit, 1 Lambert, 2 Blinn-Phong

out vec4 fragColor;

void main() {
    if (lightingMode == 0) {
        fragColor = vec4(baseColor, 1.0);
        return;
    }

    vec3 n = normalize(v_normal_ws);
    vec3 l = normalize(lightDirWS);
    float diff = max(dot(n, l), 0.0);

    vec3 color = ambientColor * baseColor + diffuseColor * baseColor * diff;

    if (lightingMode == 2 && diff > 0.0) {
        // Blinn-Phong: use the half-vector between view and light
        // instead of the reflected light direction.  Cheaper than
        // classic Phong (no reflect()) and visually similar.
        vec3 v = normalize(cameraPosWS - v_position_ws);
        vec3 h = normalize(l + v);
        float spec = pow(max(dot(n, h), 0.0), shininess);
        color += specularColor * spec;
    }

    fragColor = vec4(color, 1.0);
}
