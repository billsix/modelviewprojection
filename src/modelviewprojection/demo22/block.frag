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
in vec2 v_texcoord;

uniform vec3  flatColor;       // used when useTexture is false
uniform bool  useLighting;     // turn the lighting calculation on/off
uniform bool  useTexture;      // sample from `tex` instead of using flatColor
uniform bool  useShadows;      // sample shadowMap and darken accordingly
uniform vec3  lightDirWS;      // direction *toward* the light, normalized
uniform vec3  ambientColor;
uniform vec3  diffuseColor;
uniform sampler2D tex;
uniform sampler2D shadowMap;
uniform mat4  lightSpaceMatrix;

out vec4 fragColor;

// Returns 1.0 if this fragment is in shadow, 0.0 if it's lit.
//
// Shadow mapping in three steps:
//   1.  Re-project the fragment's world-space position into the
//       light's clip space using the same matrix the depth pass used.
//   2.  Convert that clip-space point to texture coords [0,1] and
//       sample the depth map at (x,y).  The sample is the depth of
//       whatever surface was *closest* to the light along that ray.
//   3.  Compare the fragment's own light-space depth against the
//       sample.  If the fragment is farther, something else was in
//       front of it -- it's in shadow.
//
// The bias term cancels out "shadow acne" -- the self-shadowing
// stripes that show up when a flat surface partially shadows itself
// due to depth-buffer precision.  Steeper angles need more bias,
// which is what the (1 - dot(N, L)) factor encodes.
float shadow_factor() {
    vec4 lightSpacePos = lightSpaceMatrix * vec4(v_position_ws, 1.0);
    vec3 projCoord = lightSpacePos.xyz / lightSpacePos.w;
    projCoord = projCoord * 0.5 + 0.5;            // [-1,1] -> [0,1]

    // Anything past the light's far plane is treated as lit.  Same
    // for points behind the light (z<0 in NDC) -- those can't be in
    // the depth map at all.
    if (projCoord.z > 1.0 || projCoord.z < 0.0) return 0.0;
    if (projCoord.x < 0.0 || projCoord.x > 1.0) return 0.0;
    if (projCoord.y < 0.0 || projCoord.y > 1.0) return 0.0;

    vec3 n = normalize(v_normal_ws);
    vec3 l = normalize(lightDirWS);
    float bias = max(0.005 * (1.0 - dot(n, l)), 0.0008);

    float closest = texture(shadowMap, projCoord.xy).r;
    return projCoord.z - bias > closest ? 1.0 : 0.0;
}

void main() {
    vec3 base = useTexture ? texture(tex, v_texcoord).rgb : flatColor;

    if (useLighting) {
        vec3 n = normalize(v_normal_ws);
        float diff = max(dot(n, normalize(lightDirWS)), 0.0);
        // Shadow only attenuates the *direct* diffuse term -- ambient
        // light reaches everywhere by definition.  Standard model.
        float shadow = useShadows ? shadow_factor() : 0.0;
        vec3 lit = ambientColor * base
                 + diffuseColor * base * diff * (1.0 - shadow);
        fragColor = vec4(lit, 1.0);
    } else {
        fragColor = vec4(base, 1.0);
    }
}
