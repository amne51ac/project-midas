import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Line, useTexture } from '@react-three/drei';
import * as THREE from 'three';
import type { AtlasBrightStar } from '../../data/atlasSkyOverlay';
import type { AtlasBundle, AtlasCluster, AtlasStar } from '../../data/atlasTypes';
import {
  SKY_RADIUS,
  SKY_TEXTURE_Y_ROT,
  type AtlasColorMode,
  buildStarBuffers,
  clusterRingPoints,
  raDecToVector3,
} from '../../utils/atlasSphere';
import { BrightStarLayer, ConstellationLayer } from './AtlasSkyLayers';
import type { AtlasPick } from './atlasPickTypes';

interface FlyTarget {
  ra: number;
  dec: number;
}

interface Props {
  bundle: AtlasBundle;
  visible: AtlasStar[];
  activeClusters: Set<string>;
  colorMode: AtlasColorMode;
  flyTarget: FlyTarget | null;
  onFlyComplete: () => void;
  onHover: (pick: AtlasPick | null) => void;
  onSelect: (pick: AtlasPick | null) => void;
  showConstellations: boolean;
  showBrightStars: boolean;
  brightStars: AtlasBrightStar[];
  constellations: { id: string; name: string; points: [number, number][] }[];
}

export const FOV_MIN = 8;
export const FOV_MAX = 95;
const LAT_LIMIT = Math.PI / 2 - 0.05;
const DRAG_SPEED = 0.003;
const DRAG_THRESHOLD = 5;

function SkySphere() {
  const texture = useTexture('/images/all-sky-milkyway.jpg');
  useEffect(() => {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 16;
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
  }, [texture]);

  return (
    <mesh rotation={[0, SKY_TEXTURE_Y_ROT, 0]} scale={[-1, 1, 1]}>
      <sphereGeometry args={[SKY_RADIUS, 128, 64]} />
      <meshBasicMaterial map={texture} side={THREE.BackSide} toneMapped={false} />
    </mesh>
  );
}

function DataStars({
  stars,
  colorMode,
  pointsRef,
}: {
  stars: AtlasStar[];
  colorMode: AtlasColorMode;
  pointsRef: React.RefObject<THREE.Points>;
}) {
  const buffers = useMemo(() => buildStarBuffers(stars, colorMode), [stars, colorMode]);

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[buffers.positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[buffers.colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={4.2}
        sizeAttenuation
        vertexColors
        transparent
        opacity={0.98}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
        toneMapped={false}
      />
    </points>
  );
}

function ClusterRing({ cluster }: { cluster: AtlasCluster }) {
  const points = useMemo(
    () => clusterRingPoints(cluster.ra, cluster.dec, cluster.radiusDeg),
    [cluster],
  );

  return (
    <Line
      points={points}
      color="#9a9a9a"
      transparent
      opacity={0.35}
      lineWidth={1}
    />
  );
}

function clampLat(lat: number): number {
  return THREE.MathUtils.clamp(lat, -LAT_LIMIT, LAT_LIMIT);
}

function directionToLonLat(dir: THREE.Vector3): { lon: number; lat: number } {
  const n = dir.clone().normalize();
  return {
    lon: Math.atan2(n.z, n.x),
    lat: clampLat(Math.asin(THREE.MathUtils.clamp(n.y, -1, 1))),
  };
}

function shortestLonDelta(from: number, to: number): number {
  let delta = to - from;
  while (delta > Math.PI) delta -= Math.PI * 2;
  while (delta < -Math.PI) delta += Math.PI * 2;
  return delta;
}

function PlanetariumControls({
  flyTarget,
  onComplete,
  onHover,
  onSelect,
  dataStarsRef,
  brightStarsRef,
  memberStars,
  brightStars,
  showBrightStars,
}: {
  flyTarget: FlyTarget | null;
  onComplete: () => void;
  onHover: (pick: AtlasPick | null) => void;
  onSelect: (pick: AtlasPick | null) => void;
  dataStarsRef: React.RefObject<THREE.Points>;
  brightStarsRef: React.RefObject<THREE.Points>;
  memberStars: AtlasStar[];
  brightStars: AtlasBrightStar[];
  showBrightStars: boolean;
}) {
  const { camera, gl } = useThree();
  const lon = useRef(0);
  const lat = useRef(0);
  const velLon = useRef(0);
  const velLat = useRef(0);
  const dragging = useRef(false);
  const pointerDown = useRef(false);
  const lastPtr = useRef({ x: 0, y: 0 });
  const downPtr = useRef({ x: 0, y: 0 });
  const flyProgress = useRef<number | null>(null);
  const flyStart = useRef({ lon: 0, lat: 0 });
  const flyEnd = useRef({ lon: 0, lat: 0 });
  const lookDir = useRef(new THREE.Vector3());
  const raycaster = useMemo(() => new THREE.Raycaster(), []);
  const ndc = useRef(new THREE.Vector2());

  const applyLook = () => {
    camera.position.set(0, 0, 0);
    const cosLat = Math.cos(lat.current);
    lookDir.current.set(
      cosLat * Math.cos(lon.current),
      Math.sin(lat.current),
      cosLat * Math.sin(lon.current),
    );
    camera.up.set(0, 1, 0);
    camera.lookAt(lookDir.current);
  };

  const pickThreshold = () => {
    const cam = camera as THREE.PerspectiveCamera;
    return 0.45 * (cam.fov / 68);
  };

  const pickAt = (clientX: number, clientY: number): AtlasPick | null => {
    const canvas = gl.domElement;
    const rect = canvas.getBoundingClientRect();
    ndc.current.set(
      ((clientX - rect.left) / rect.width) * 2 - 1,
      -((clientY - rect.top) / rect.height) * 2 + 1,
    );
    raycaster.setFromCamera(ndc.current, camera);
    raycaster.params.Points = { threshold: pickThreshold() };

    if (dataStarsRef.current) {
      const memberHits = raycaster.intersectObject(dataStarsRef.current);
      if (memberHits.length > 0) {
        const idx = memberHits[0].index ?? 0;
        const star = memberStars[idx];
        if (star) return { type: 'member', star };
      }
    }

    if (showBrightStars && brightStarsRef.current) {
      const brightHits = raycaster.intersectObject(brightStarsRef.current);
      if (brightHits.length > 0) {
        const idx = brightHits[0].index ?? 0;
        const star = brightStars[idx];
        if (star) return { type: 'bright', star };
      }
    }

    return null;
  };

  useEffect(() => {
    const start = directionToLonLat(raDecToVector3(0, 0, 1));
    lon.current = start.lon;
    lat.current = start.lat;
    applyLook();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- one-time camera orientation
  }, []);

  useEffect(() => {
    if (!flyTarget) return;
    flyStart.current = { lon: lon.current, lat: lat.current };
    flyEnd.current = directionToLonLat(raDecToVector3(flyTarget.ra, flyTarget.dec, 1));
    flyProgress.current = 0;
    velLon.current = 0;
    velLat.current = 0;
  }, [flyTarget]);

  useEffect(() => {
    const canvas = gl.domElement;

    const onPointerDown = (event: PointerEvent) => {
      if (event.button !== 0) return;
      pointerDown.current = true;
      dragging.current = false;
      flyProgress.current = null;
      velLon.current = 0;
      velLat.current = 0;
      lastPtr.current = { x: event.clientX, y: event.clientY };
      downPtr.current = { x: event.clientX, y: event.clientY };
      canvas.setPointerCapture(event.pointerId);
    };

    const endPointer = (event: PointerEvent) => {
      if (!pointerDown.current) return;
      const moved = Math.hypot(
        event.clientX - downPtr.current.x,
        event.clientY - downPtr.current.y,
      );
      if (!dragging.current && moved < DRAG_THRESHOLD) {
        onSelect(pickAt(event.clientX, event.clientY));
      }
      pointerDown.current = false;
      dragging.current = false;
      if (canvas.hasPointerCapture(event.pointerId)) {
        canvas.releasePointerCapture(event.pointerId);
      }
    };

    const onPointerMove = (event: PointerEvent) => {
      if (!pointerDown.current) {
        onHover(pickAt(event.clientX, event.clientY));
        return;
      }

      const dx = event.clientX - lastPtr.current.x;
      const dy = event.clientY - lastPtr.current.y;
      const moved = Math.hypot(event.clientX - downPtr.current.x, event.clientY - downPtr.current.y);

      if (!dragging.current && moved >= DRAG_THRESHOLD) {
        dragging.current = true;
        onHover(null);
      }

      if (!dragging.current) return;

      lastPtr.current = { x: event.clientX, y: event.clientY };
      lon.current -= dx * DRAG_SPEED;
      lat.current = clampLat(lat.current + dy * DRAG_SPEED);
      velLon.current = -dx * DRAG_SPEED;
      velLat.current = dy * DRAG_SPEED;
      applyLook();
    };

    const onPointerLeave = () => onHover(null);

    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const cam = camera as THREE.PerspectiveCamera;
      cam.fov = THREE.MathUtils.clamp(cam.fov + event.deltaY * 0.04, FOV_MIN, FOV_MAX);
      cam.updateProjectionMatrix();
    };

    canvas.addEventListener('pointerdown', onPointerDown);
    canvas.addEventListener('pointerup', endPointer);
    canvas.addEventListener('pointercancel', endPointer);
    canvas.addEventListener('pointermove', onPointerMove);
    canvas.addEventListener('pointerleave', onPointerLeave);
    canvas.addEventListener('wheel', onWheel, { passive: false });
    return () => {
      canvas.removeEventListener('pointerdown', onPointerDown);
      canvas.removeEventListener('pointerup', endPointer);
      canvas.removeEventListener('pointercancel', endPointer);
      canvas.removeEventListener('pointermove', onPointerMove);
      canvas.removeEventListener('pointerleave', onPointerLeave);
      canvas.removeEventListener('wheel', onWheel);
    };
  }, [
    camera,
    gl.domElement,
    onHover,
    onSelect,
    memberStars,
    brightStars,
    showBrightStars,
    dataStarsRef,
    brightStarsRef,
    raycaster,
  ]);

  useFrame((_, delta) => {
    if (flyProgress.current != null) {
      flyProgress.current = Math.min(1, flyProgress.current + delta * 1.2);
      const eased = 1 - (1 - flyProgress.current) ** 3;
      const dLon = shortestLonDelta(flyStart.current.lon, flyEnd.current.lon);
      lon.current = flyStart.current.lon + dLon * eased;
      lat.current = flyStart.current.lat + (flyEnd.current.lat - flyStart.current.lat) * eased;
      applyLook();
      if (flyProgress.current >= 1) {
        flyProgress.current = null;
        onComplete();
      }
      return;
    }

    if (
      !dragging.current &&
      (Math.abs(velLon.current) > 1e-5 || Math.abs(velLat.current) > 1e-5)
    ) {
      lon.current += velLon.current;
      lat.current = clampLat(lat.current + velLat.current);
      const decay = Math.exp(-6 * delta);
      velLon.current *= decay;
      velLat.current *= decay;
      applyLook();
    }
  });

  return null;
}

export function AtlasScene({
  bundle,
  visible,
  activeClusters,
  colorMode,
  flyTarget,
  onFlyComplete,
  onHover,
  onSelect,
  showConstellations,
  showBrightStars,
  brightStars,
  constellations,
}: Props) {
  const dataStarsRef = useRef<THREE.Points>(null!);
  const brightStarsRef = useRef<THREE.Points>(null!);
  const activeHulls = bundle.clusters.filter((c) => activeClusters.has(c.id));

  return (
    <>
      <color attach="background" args={['#090909']} />
      <ambientLight intensity={0.15} />
      <SkySphere />
      {showConstellations && <ConstellationLayer constellations={constellations} />}
      {showBrightStars && <BrightStarLayer stars={brightStars} pointsRef={brightStarsRef} />}
      <DataStars stars={visible} colorMode={colorMode} pointsRef={dataStarsRef} />
      {activeHulls.map((c) => (
        <ClusterRing key={c.id} cluster={c} />
      ))}
      <PlanetariumControls
        flyTarget={flyTarget}
        onComplete={onFlyComplete}
        onHover={onHover}
        onSelect={onSelect}
        dataStarsRef={dataStarsRef}
        brightStarsRef={brightStarsRef}
        memberStars={visible}
        brightStars={brightStars}
        showBrightStars={showBrightStars}
      />
    </>
  );
}
