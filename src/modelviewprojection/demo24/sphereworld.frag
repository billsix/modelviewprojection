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

in vec3 v_position_ws;
in vec3 v_normal_ws;
in vec2 v_uv;

uniform sampler2D tex;
uniform vec3  baseColor;
uniform vec3  cameraPosWS;
uniform vec3  lightPosWS;          // positional light, world-space
uniform vec3  ambientColor;
uniform vec3  diffuseColor;
uniform vec3  specularColor;
uniform float shininess;
uniform int   renderMode;          // 0 shadow, 1 lit+textured, 2 unlit flat

out vec4 fragColor;

void main() {
    // Mode 0:  this fragment is part of a planar-projected silhouette
    // drawn on the ground.  The host has already squashed geometry to
    // the ground plane via a special model matrix; we just emit a
    // semi-transparent black, and the host's GL_BLEND state composites
    // it over the lit ground.  Stencil prevents overlap doubling.
    if (renderMode == 0) {
        fragColor = vec4(0.0, 0.0, 0.0, 0.6);
        return;
    }

    // Mode 2:  flat color, no texture, no lighting.  Used for the
    // wireframe overlay.
    if (renderMode == 2) {
        fragColor = vec4(baseColor, 1.0);
        return;
    }

    // Mode 1:  lit + textured Blinn-Phong.  baseColor is a tint on top
    // of the texture (white = no tint).
    vec3 albedo = texture(tex, v_uv).rgb * baseColor;

    vec3 n = normalize(v_normal_ws);
    vec3 l = normalize(lightPosWS - v_position_ws);
    float diff = max(dot(n, l), 0.0);

    vec3 color = ambientColor * albedo + diffuseColor * albedo * diff;

    if (diff > 0.0) {
        vec3 v = normalize(cameraPosWS - v_position_ws);
        vec3 h = normalize(l + v);
        float spec = pow(max(dot(n, h), 0.0), shininess);
        color += specularColor * spec;
    }

    fragColor = vec4(color, 1.0);
}
