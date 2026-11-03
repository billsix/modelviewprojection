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

#version 330 core

// The texExpToPng PNG is a glyph MASK: dvipng in this image renders the formula
// black-on-transparent regardless of `--fg`, but the alpha channel carries the
// glyph coverage.  So paint the glyphs a fixed colour here, using that alpha as
// the mask, rather than reading the texture's (black) RGB.  Straight (non-
// premultiplied) alpha; the caller enables SRC_ALPHA / ONE_MINUS_SRC_ALPHA.
in vec2 v_uv;

uniform sampler2D tex;

out vec4 fragColor;

void main()
{
    float coverage = texture(tex, v_uv).a;
    fragColor = vec4(1.0, 1.0, 1.0, coverage);
}
