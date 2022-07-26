#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec4 color_in;

uniform mat4 mvpMatrix;

out VS_OUT {
  vec4 color;
} vs_out;


void main()
{
   gl_Position = mvpMatrix * vec4(position,1.0);
   vs_out.color = color_in;
}
