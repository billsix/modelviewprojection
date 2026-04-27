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
uniform sampler2D shadowMap;
uniform mat4  lightSpaceMatrix;
uniform vec3  baseColor;
uniform vec3  cameraPosWS;
uniform vec3  lightPosWS;          // positional light, world-space
uniform vec3  ambientColor;
uniform vec3  diffuseColor;
uniform vec3  specularColor;
uniform float shininess;
uniform bool  useShadows;
uniform int   renderMode;          // 1 lit+textured, 2 unlit flat

out vec4 fragColor;

// 1.0 if this fragment is in shadow, 0.0 if lit.  Same shape as
// demo22's helper; see the comment in block.frag for the recipe.
float shadow_factor(vec3 normal_ws, vec3 light_dir_ws) {
    vec4 lightSpacePos = lightSpaceMatrix * vec4(v_position_ws, 1.0);
    vec3 projCoord = lightSpacePos.xyz / lightSpacePos.w;
    projCoord = projCoord * 0.5 + 0.5;

    if (projCoord.z > 1.0 || projCoord.z < 0.0) return 0.0;
    if (projCoord.x < 0.0 || projCoord.x > 1.0) return 0.0;
    if (projCoord.y < 0.0 || projCoord.y > 1.0) return 0.0;

    float bias = max(0.005 * (1.0 - dot(normal_ws, light_dir_ws)), 0.0008);
    float closest = texture(shadowMap, projCoord.xy).r;
    return projCoord.z - bias > closest ? 1.0 : 0.0;
}

void main() {
    // Mode 2:  flat color, no texture, no lighting.  Used for the
    // wireframe overlay AND the yellow light-position marker.  Skips
    // shadow sampling -- a marker shouldn't cast a shadow on itself.
    if (renderMode == 2) {
        fragColor = vec4(baseColor, 1.0);
        return;
    }

    // Mode 1:  lit + textured Blinn-Phong with shadow attenuation.
    vec3 albedo = texture(tex, v_uv).rgb * baseColor;

    vec3 n = normalize(v_normal_ws);
    vec3 l = normalize(lightPosWS - v_position_ws);
    float diff = max(dot(n, l), 0.0);

    float shadow = useShadows ? shadow_factor(n, l) : 0.0;

    vec3 color = ambientColor * albedo
               + diffuseColor * albedo * diff * (1.0 - shadow);

    if (diff > 0.0 && shadow < 1.0) {
        vec3 v = normalize(cameraPosWS - v_position_ws);
        vec3 h = normalize(l + v);
        float spec = pow(max(dot(n, h), 0.0), shininess);
        color += specularColor * spec * (1.0 - shadow);
    }

    fragColor = vec4(color, 1.0);
}
