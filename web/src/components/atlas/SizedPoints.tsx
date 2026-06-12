import { useMemo } from 'react';
import * as THREE from 'three';

const vertexShader = /* glsl */ `
  attribute float size;
  attribute vec3 color;
  varying vec3 vColor;
  void main() {
    vColor = color;
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = size * (320.0 / -mvPosition.z);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const fragmentShader = /* glsl */ `
  varying vec3 vColor;
  uniform float opacity;
  void main() {
    vec2 c = gl_PointCoord - vec2(0.5);
    float r = dot(c, c);
    if (r > 0.25) discard;
    float edge = smoothstep(0.22, 0.12, r);
    gl_FragColor = vec4(vColor, opacity * edge);
  }
`;

interface Props {
  positions: Float32Array;
  colors: Float32Array;
  sizes: Float32Array;
  opacity?: number;
  blending?: THREE.Blending;
}

export function SizedPoints({
  positions,
  colors,
  sizes,
  opacity = 0.95,
  blending = THREE.NormalBlending,
}: Props) {
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader,
        fragmentShader,
        uniforms: { opacity: { value: opacity } },
        transparent: true,
        depthWrite: false,
        blending,
        toneMapped: false,
      }),
    [opacity, blending],
  );

  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    g.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    return g;
  }, [positions, colors, sizes]);

  return <points geometry={geometry} material={material} />;
}

interface MonoProps {
  positions: Float32Array;
  sizes: Float32Array;
  color: string;
  opacity?: number;
}

export function SizedMonoPoints({
  positions,
  sizes,
  color,
  opacity = 0.95,
}: MonoProps) {
  const { colors } = useMemo(() => {
    const c = new THREE.Color(color);
    const colors = new Float32Array((positions.length / 3) * 3);
    for (let i = 0; i < colors.length; i += 3) {
      colors[i] = c.r;
      colors[i + 1] = c.g;
      colors[i + 2] = c.b;
    }
    return { colors };
  }, [positions, color]);

  return (
    <SizedPoints
      positions={positions}
      colors={colors}
      sizes={sizes}
      opacity={opacity}
      blending={THREE.AdditiveBlending}
    />
  );
}
