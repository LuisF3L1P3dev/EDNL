"""Luz difusa para a cidade, conservando cores e sombras dos modelos low-poly."""
from ursina import Shader
from ursina.shaders import lit_with_shadows_shader

# O vértice reutiliza a integração do Ursina com a câmera e o mapa de sombras.
# A iluminação multiplicativa evita clarear o asfalto e estourar as cores claras.
shader_cidade = Shader(
    name="nexus_cidade", language=Shader.GLSL,
    vertex=lit_with_shadows_shader.vertex,
    fragment='''#version 150
uniform struct {
    vec4 position;
    vec3 color;
    vec3 attenuation;
    vec3 spotDirection;
    float spotCosCutoff;
    float spotExponent;
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[1];
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform float sombra_ativa;
uniform float shadow_bias;
in vec2 texcoords;
in vec4 vertex_color;
in vec3 normal_vector;
in vec3 vertex_position;
in vec4 shadow_coord[1];
out vec4 fragment_color;
void main() {
    vec4 base = texture(p3d_Texture0, texcoords) * p3d_ColorScale * vertex_color;
    vec3 luz = normalize(p3d_LightSource[0].position.xyz - vertex_position * p3d_LightSource[0].position.w);
    float difusa = max(0.0, dot(normalize(normal_vector), luz));
    float visibilidade = 1.0;
    if (sombra_ativa > 0.5) {
        vec4 coordenada = shadow_coord[0];
        coordenada.z += shadow_bias;
        visibilidade = 0.0;
        for (int x = 0; x < 2; ++x) {
            for (int y = 0; y < 2; ++y) {
                vec4 amostra = coordenada;
                amostra.xy += (vec2(x, y) - 0.5) * 0.0012 * coordenada.w;
                visibilidade += textureProj(p3d_LightSource[0].shadowMap, amostra);
            }
        }
        visibilidade *= 0.25;
    }
    vec3 ambiente = vec3(0.56, 0.60, 0.65);
    vec3 sol = p3d_LightSource[0].color * difusa * (0.20 + visibilidade * 0.44);
    fragment_color = vec4(base.rgb * (ambiente + sol), base.a);
}
''',
    default_input={"texture_scale": (1, 1), "texture_offset": (0, 0),
                   "shadow_bias": .001, "sombra_ativa": 1.},
)
