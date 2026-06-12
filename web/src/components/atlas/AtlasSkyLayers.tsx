import { useMemo, type RefObject } from 'react';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import type { AtlasBrightStar, AtlasConstellation } from '../../data/atlasSkyOverlay';
import { STAR_RADIUS, raDecToVector3 } from '../../utils/atlasSphere';

export function ConstellationLayer({ constellations }: { constellations: AtlasConstellation[] }) {
  return (
    <>
      {constellations.map((c) => {
        const points = c.points.map(([ra, dec]) => raDecToVector3(ra, dec, STAR_RADIUS - 1));
        return (
          <Line
            key={c.id}
            points={points}
            color="#d4a72c"
            transparent
            opacity={0.28}
            lineWidth={1}
          />
        );
      })}
    </>
  );
}

export function BrightStarLayer({
  stars,
  pointsRef,
}: {
  stars: AtlasBrightStar[];
  pointsRef: RefObject<THREE.Points>;
}) {
  const positions = useMemo(() => {
    const buf = new Float32Array(stars.length * 3);
    stars.forEach((star, i) => {
      const v = raDecToVector3(star.ra, star.dec, STAR_RADIUS - 0.5);
      buf[i * 3] = v.x;
      buf[i * 3 + 1] = v.y;
      buf[i * 3 + 2] = v.z;
    });
    return buf;
  }, [stars]);

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={5}
        sizeAttenuation
        color="#f0f0f0"
        transparent
        opacity={0.92}
        depthWrite={false}
        toneMapped={false}
      />
    </points>
  );
}
