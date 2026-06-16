import { useMemo, type MutableRefObject } from 'react';
import { Line } from '@react-three/drei';
import type { AtlasConstellation } from '../../data/atlasConstellationData';
import type { AtlasReferenceObject } from '../../data/atlasReferenceObjects';
import {
  STAR_RADIUS,
  apparentMagPointSize,
  buildBrightStarBuffers,
  raDecToVector3,
  shortStarName,
} from '../../utils/atlasSphere';
import { AtlasSkyLabel } from './AtlasSkyLabel';
import { SizedPoints } from './SizedPoints';

/** Obscure / small constellations — drawn and labeled more faintly than primary figures. */
const SECONDARY_CONSTELLATION_IDS = new Set([
  'leo-minor',
  'delphinus',
  'corona-borealis',
  'corona-australis',
  'triangulum',
  'lupus',
  'norma',
  'grus',
  'phoenix',
  'sculptor',
  'fornax',
  'coma-berenices',
  'puppis',
  'vela',
  'hydra',
  'cetus',
  'libra',
  'capricornus',
  'aquarius',
  'pisces',
  'aries',
  'ophiuchus',
  'eridanus',
]);

const LINE_STYLE = {
  primary: {
    major: { color: '#9a9078', opacity: 0.22, lineWidth: 1 },
    minor: { color: '#8a8270', opacity: 0.1, lineWidth: 1 },
  },
  secondary: {
    major: { color: '#787368', opacity: 0.12, lineWidth: 1 },
    minor: { color: '#6a655c', opacity: 0.05, lineWidth: 1 },
  },
} as const;

function constellationLabelAnchor(c: AtlasConstellation): [number, number] {
  if (c.label) return c.label;
  const flat = c.major.flat();
  if (flat.length === 0) return [0, 0];
  const ra = flat.reduce((s, p) => s + p[0], 0) / flat.length;
  const dec = flat.reduce((s, p) => s + p[1], 0) / flat.length;
  return [ra, dec];
}

export function ConstellationLayer({
  constellations,
  portal,
}: {
  constellations: AtlasConstellation[];
  portal: MutableRefObject<HTMLElement>;
}) {
  return (
    <>
      {constellations.map((c) => {
        const tier = SECONDARY_CONSTELLATION_IDS.has(c.id) ? 'secondary' : 'primary';
        const styles = LINE_STYLE[tier];
        const labelVariant =
          tier === 'secondary' ? 'constellation-secondary' : 'constellation';
        const [labelRa, labelDec] = constellationLabelAnchor(c);
        const labelPos = raDecToVector3(labelRa, labelDec, STAR_RADIUS - 2);

        return (
          <group key={c.id}>
            {c.major.map((path, i) => {
              const points = path.map(([ra, dec]) => raDecToVector3(ra, dec, STAR_RADIUS - 1));
              return (
                <Line
                  key={`${c.id}-major-${i}`}
                  points={points}
                  color={styles.major.color}
                  transparent
                  opacity={styles.major.opacity}
                  lineWidth={styles.major.lineWidth}
                />
              );
            })}
            {c.minor?.map((path, i) => {
              const points = path.map(([ra, dec]) => raDecToVector3(ra, dec, STAR_RADIUS - 1));
              return (
                <Line
                  key={`${c.id}-minor-${i}`}
                  points={points}
                  color={styles.minor.color}
                  transparent
                  opacity={styles.minor.opacity}
                  lineWidth={styles.minor.lineWidth}
                />
              );
            })}
            <AtlasSkyLabel position={labelPos} variant={labelVariant} portal={portal}>
              {c.name}
            </AtlasSkyLabel>
          </group>
        );
      })}
    </>
  );
}

function labelVariant(star: AtlasReferenceObject): 'star' | 'dso' {
  return star.kind === 'star' ? 'star' : 'dso';
}

export function BrightStarLayer({
  stars,
  portal,
}: {
  stars: AtlasReferenceObject[];
  portal: MutableRefObject<HTMLElement>;
}) {
  const { positions, sizes, colors, glowSizes } = useMemo(() => {
    const base = buildBrightStarBuffers(stars);
    const glowSizes = new Float32Array(base.sizes.length);
    for (let i = 0; i < base.sizes.length; i++) {
      glowSizes[i] = base.sizes[i] * 1.7;
    }
    return { ...base, glowSizes };
  }, [stars]);

  const glowColors = useMemo(() => {
    const glow = new Float32Array(colors.length);
    for (let i = 0; i < colors.length; i += 3) {
      glow[i] = colors[i] * 0.85;
      glow[i + 1] = colors[i + 1] * 0.85;
      glow[i + 2] = colors[i + 2] * 0.85;
    }
    return glow;
  }, [colors]);

  const labeled = useMemo(() => stars.filter((s) => s.label !== false), [stars]);

  return (
    <group>
      <SizedPoints positions={positions} colors={glowColors} sizes={glowSizes} opacity={0.16} />
      <SizedPoints positions={positions} colors={colors} sizes={sizes} opacity={0.96} />
      {labeled.map((star) => {
        const pos = raDecToVector3(star.ra, star.dec, STAR_RADIUS - 0.5);
        const labelOffset = pos
          .clone()
          .normalize()
          .multiplyScalar(STAR_RADIUS - 0.5 + apparentMagPointSize(star.mag) * 0.1);
        return (
          <AtlasSkyLabel key={star.id} position={labelOffset} variant={labelVariant(star)} portal={portal}>
            {shortStarName(star.name)}
          </AtlasSkyLabel>
        );
      })}
    </group>
  );
}
