import * as d3 from 'd3';
import * as THREE from 'three';
import type { AtlasStar } from '../data/atlasTypes';

export const SKY_RADIUS = 500;
export const STAR_RADIUS = 498;
export const SKY_TEXTURE_Y_ROT = Math.PI * 0.52;

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

 export function starPointSize(g: number | undefined): number {
   if (g == null) return 2.8;
   return d3.scaleLinear().domain([8, 18]).range([5.5, 1.6]).clamp(true)(g);
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

     sizes[i] = starPointSize(star.g);
   });

   return { positions, colors, sizes, stars };
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
