#version 330 core

// Sample the label texture (white glyphs on a transparent background, produced by
// ``texExpToPng --bg Transparent --fg "rgb 1 1 1"``).  Straight (non-premultiplied)
// alpha; the caller enables SRC_ALPHA / ONE_MINUS_SRC_ALPHA blending.
in vec2 v_uv;

uniform sampler2D tex;

out vec4 fragColor;

void main()
{
    fragColor = texture(tex, v_uv);
}
