import * as d3 from 'd3';
import * as THREE from 'three';
import type { AtlasReferenceKind, AtlasReferenceObject } from '../data/atlasReferenceObjects';
import type { AtlasStar } from '../data/atlasTypes';

export const SKY_RADIUS = 500;
export const STAR_RADIUS = 498;

export type AtlasColorMode = 'pBinary' | 'pMember' | 'malofeeva';

export function raDecToVector3(raDeg: number, decDeg: number, radius = 1): THREE.Vector3 {
  const ra = (raDeg * Math.PI) / 180;
  const dec = (decDeg * Math.PI) / 180;
  return new THREE.Vector3(
    radius * Math.cos(dec) * Math.cos(ra),
    radius * Math.sin(dec),
    radius * Math.cos(dec) * Math.sin(ra),
  );
}

export function starColorHex(star: AtlasStar, mode: AtlasColorMode): string {
  if (mode === 'malofeeva') return star.malofeeva ? '#fbbf24' : '#64748b';
  const t = mode === 'pBinary' ? star.pBinary : (star.pMember ?? 0);
  return d3.interpolatePlasma(Math.min(1, Math.max(0, t)));
}

/** Visual point size from Gaia G (brighter = larger). */
export function memberPointSize(g: number | undefined): number {
  if (g == null) return 6;
  return d3.scaleLinear().domain([8, 18]).range([10, 3.5]).clamp(true)(g);
}

/** Visual point size from apparent magnitude (brighter = larger). */
export function apparentMagPointSize(mag: number): number {
  return d3.scaleLinear().domain([-1.5, 6]).range([16, 4]).clamp(true)(mag);
}

/** Pick radius in degrees — scales with zoom but stays generous. */
export function pickAngleDeg(fovDeg: number, kind: 'member' | 'bright'): number {
  const base = kind === 'member' ? 1.35 : 1.15;
  const scaled = base * (fovDeg / 68);
  const min = kind === 'member' ? 0.55 : 0.5;
  const max = kind === 'member' ? 2.4 : 2.0;
  return THREE.MathUtils.clamp(scaled, min, max);
}

const _starDir = new THREE.Vector3();

function angularSeparationDeg(rayDir: THREE.Vector3, ra: number, dec: number): number {
  _starDir.copy(raDecToVector3(ra, dec, 1)).normalize();
  const dot = THREE.MathUtils.clamp(rayDir.dot(_starDir), -1, 1);
  return THREE.MathUtils.radToDeg(Math.acos(dot));
}

export function pickMemberStar(
  ray: THREE.Ray,
  stars: AtlasStar[],
  fovDeg: number,
): AtlasStar | null {
  const rayDir = ray.direction;
  const limit = pickAngleDeg(fovDeg, 'member');
  let best: { star: AtlasStar; angle: number } | null = null;

  for (const star of stars) {
    const angle = angularSeparationDeg(rayDir, star.ra, star.dec);
    if (angle <= limit && (!best || angle < best.angle)) {
      best = { star, angle };
    }
  }
  return best?.star ?? null;
}

export function pickBrightStar(
  ray: THREE.Ray,
  stars: AtlasReferenceObject[],
  fovDeg: number,
): AtlasReferenceObject | null {
  const rayDir = ray.direction;
  const limit = pickAngleDeg(fovDeg, 'bright');
  let best: { star: AtlasReferenceObject; angle: number } | null = null;

  for (const star of stars) {
    const angle = angularSeparationDeg(rayDir, star.ra, star.dec);
    if (angle <= limit && (!best || angle < best.angle)) {
      best = { star, angle };
    }
  }
  return best?.star ?? null;
}

export interface StarBuffers {
  positions: Float32Array;
  colors: Float32Array;
  sizes: Float32Array;
  stars: AtlasStar[];
}

export function buildStarBuffers(stars: AtlasStar[], mode: AtlasColorMode): StarBuffers {
  const positions = new Float32Array(stars.length * 3);
  const colors = new Float32Array(stars.length * 3);
  const sizes = new Float32Array(stars.length);
  const color = new THREE.Color();

  stars.forEach((star, i) => {
    const v = raDecToVector3(star.ra, star.dec, STAR_RADIUS);
    positions[i * 3] = v.x;
    positions[i * 3 + 1] = v.y;
    positions[i * 3 + 2] = v.z;

    color.set(starColorHex(star, mode));
    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;

    sizes[i] = memberPointSize(star.g);
  });

  return { positions, colors, sizes, stars };
}

function referenceKindColor(kind: AtlasReferenceKind): THREE.Color {
  switch (kind) {
    case 'galaxy':
      return new THREE.Color('#9ec5e8');
    case 'nebula':
      return new THREE.Color('#e8a8c8');
    case 'cluster':
      return new THREE.Color('#f0e6c8');
    default:
      return new THREE.Color('#f5f5f5');
  }
}

export function buildBrightStarBuffers(stars: AtlasReferenceObject[]): {
  positions: Float32Array;
  sizes: Float32Array;
  colors: Float32Array;
} {
  const positions = new Float32Array(stars.length * 3);
  const sizes = new Float32Array(stars.length);
  const colors = new Float32Array(stars.length * 3);

  stars.forEach((star, i) => {
    const v = raDecToVector3(star.ra, star.dec, STAR_RADIUS - 0.5);
    positions[i * 3] = v.x;
    positions[i * 3 + 1] = v.y;
    positions[i * 3 + 2] = v.z;
    const baseSize = apparentMagPointSize(star.mag);
    sizes[i] = star.kind === 'galaxy' || star.kind === 'nebula' ? baseSize * 1.35 : baseSize;
    const c = referenceKindColor(star.kind);
    colors[i * 3] = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;
  });

  return { positions, sizes, colors };
}

export function constellationCentroid(points: [number, number][]): { ra: number; dec: number } {
  if (points.length === 0) return { ra: 0, dec: 0 };
  const ra = d3.mean(points, (p) => p[0]) ?? 0;
  const dec = d3.mean(points, (p) => p[1]) ?? 0;
  return { ra, dec };
}

export function clusterRingPoints(
  ra: number,
  dec: number,
  radiusDeg: number,
  segments = 64,
): THREE.Vector3[] {
  const center = raDecToVector3(ra, dec, STAR_RADIUS);
  const north = new THREE.Vector3(0, 1, 0);
  let axis = new THREE.Vector3().crossVectors(center, north);
  if (axis.lengthSq() < 1e-6) axis.set(1, 0, 0);
  axis.normalize();
  const tangent = new THREE.Vector3().crossVectors(axis, center).normalize();
  const bitangent = new THREE.Vector3().crossVectors(center, tangent).normalize();
  const angular = (radiusDeg * Math.PI) / 180;

  return Array.from({ length: segments + 1 }, (_, i) => {
    const theta = (i / segments) * Math.PI * 2;
    const offset = new THREE.Vector3()
      .addScaledVector(tangent, Math.cos(theta) * angular)
      .addScaledVector(bitangent, Math.sin(theta) * angular);
    return center.clone().add(offset).normalize().multiplyScalar(STAR_RADIUS);
  });
}

export function shortStarName(name: string): string {
  return name.split('(')[0].split('·')[0].trim();
}
