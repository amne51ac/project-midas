import { useMemo, useState } from 'react';
import {
  BRIGHT_STARS,
  CHART_CENTER,
  CHART_HEIGHT,
  CHART_SCALE,
  CHART_WIDTH,
  CONSTELLATION_LINES,
  FIELD_STARS,
  FINDER_HOPS,
  M34_ANGULAR_SIZE_DEG,
  type ChartStar,
} from '../data/finderChart';

function project(ra: number, dec: number) {
  const cosDec = Math.cos((CHART_CENTER.dec * Math.PI) / 180);
  const dx = -(ra - CHART_CENTER.ra) * cosDec;
  const dy = dec - CHART_CENTER.dec;
  return {
    x: CHART_WIDTH / 2 + dx * CHART_SCALE,
    y: CHART_HEIGHT / 2 - dy * CHART_SCALE,
  };
}

function magRadius(mag: number) {
  return Math.max(1.4, 6.2 - mag * 0.85);
}

function shortLabel(name: string) {
  if (name.startsWith('M34')) return 'M34';
  if (name.includes('Double Cluster')) return 'χ Per';
  const paren = name.indexOf('(');
  if (paren > 0) return name.slice(0, paren).trim();
  return name.split(' ')[0];
}

export function ConstellationFinder() {
  const [hover, setHover] = useState<ChartStar | null>(null);

  const field = useMemo(
    () =>
      FIELD_STARS.map(([ra, dec, mag], i) => ({
        id: `field-${i}`,
        ...project(ra, dec),
        r: magRadius(mag) * 0.55,
        mag,
      })),
    [],
  );

  const stars = useMemo(
    () =>
      BRIGHT_STARS.map((s) => ({
        ...s,
        ...project(s.ra, s.dec),
        r: s.id === 'm34' ? 5 : magRadius(s.mag),
        isTarget: s.id === 'm34',
      })),
    [],
  );

  const lines = useMemo(
    () =>
      CONSTELLATION_LINES.map((c) => {
        const pts = c.points.map((p) => project(p[0], p[1]));
        const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
        return { id: c.id, d };
      }),
    [],
  );

  const hopPath = useMemo(() => {
    const pts = FINDER_HOPS.map((p) => project(p[0], p[1]));
    return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  }, []);

  const m34 = stars.find((s) => s.id === 'm34')!;

  const constLabels = useMemo(
    () => [
      { name: 'Cassiopeia', ...project(19, 62.5) },
      { name: 'Perseus', ...project(52, 53) },
      { name: 'Andromeda', ...project(22, 38) },
    ],
    [],
  );

  return (
    <div className="constellation-finder">
      <div className="constellation-finder__chart-wrap">
        <svg
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          className="constellation-finder__svg"
          role="img"
          aria-label="Finder chart for Messier 34 in Perseus, between Algol and Almach"
        >
          <defs>
            <radialGradient id="finderSky" cx="45%" cy="42%" r="72%">
              <stop offset="0%" stopColor="#152238" />
              <stop offset="100%" stopColor="#060a12" />
            </radialGradient>
            <filter id="targetGlow">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <rect width={CHART_WIDTH} height={CHART_HEIGHT} fill="url(#finderSky)" />

          {/* Milky Way band hint */}
          <ellipse
            cx={project(38, 54).x}
            cy={project(38, 54).y}
            rx={CHART_WIDTH * 0.38}
            ry={CHART_HEIGHT * 0.22}
            fill="rgba(120,140,180,0.04)"
            transform={`rotate(-28 ${project(38, 54).x} ${project(38, 54).y})`}
          />

          {/* Background field */}
          {field.map((s) => (
            <circle key={s.id} cx={s.x} cy={s.y} r={s.r} fill="#c8d4ec" opacity={0.35} />
          ))}

          {/* Constellation lines */}
          {lines.map((c) => (
            <path
              key={c.id}
              d={c.d}
              fill="none"
              stroke="#4a6088"
              strokeWidth={1.1}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={0.65}
            />
          ))}

          {/* Star-hop path */}
          <path
            d={hopPath}
            fill="none"
            stroke="#e8c547"
            strokeWidth={1.5}
            strokeDasharray="7 5"
            opacity={0.75}
          />
          {FINDER_HOPS.map((p, i) => {
            const pt = project(p[0], p[1]);
            return (
              <g key={`hop-${i}`}>
                <circle cx={pt.x} cy={pt.y} r={9} fill="rgba(232,197,71,0.12)" />
                <text
                  x={pt.x}
                  y={pt.y + 3.5}
                  textAnchor="middle"
                  className="constellation-finder__hop-num"
                >
                  {i + 1}
                </text>
              </g>
            );
          })}

          {/* M34 true angular size */}
          <circle
            cx={m34.x}
            cy={m34.y}
            r={M34_ANGULAR_SIZE_DEG * CHART_SCALE}
            fill="rgba(232,197,71,0.08)"
            stroke="#e8c547"
            strokeWidth={1}
            strokeDasharray="3 2"
            opacity={0.7}
          />

          {/* Bright stars & cluster */}
          {stars.map((o) => (
            <g
              key={o.id}
              onMouseEnter={() => setHover(o)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(o)}
              onBlur={() => setHover(null)}
              tabIndex={0}
              role="button"
              aria-label={o.name}
              className={`constellation-finder__star${o.isTarget ? ' is-target' : ''}`}
            >
              {o.isTarget ? (
                <>
                  <circle cx={o.x} cy={o.y} r={o.r + 6} fill="rgba(232,197,71,0.18)" />
                  <circle cx={o.x} cy={o.y} r={o.r} fill="#e8c547" filter="url(#targetGlow)" />
                  <text
                    x={o.x + 10}
                    y={o.y - 8}
                    className="constellation-finder__star-label constellation-finder__star-label--target"
                  >
                    {shortLabel(o.name)}
                  </text>
                </>
              ) : (
                <>
                  <circle cx={o.x} cy={o.y} r={o.r} fill="#eef2ff" opacity={0.92} />
                  {o.label && (
                    <text
                      x={o.x + o.r + 3}
                      y={o.y + 3}
                      className="constellation-finder__star-label"
                    >
                      {shortLabel(o.name)}
                    </text>
                  )}
                </>
              )}
            </g>
          ))}

          {/* Constellation names */}
          {constLabels.map((c) => (
            <text
              key={c.name}
              x={c.x}
              y={c.y}
              textAnchor="middle"
              className="constellation-finder__const-label"
            >
              {c.name}
            </text>
          ))}

          {/* Compass */}
          <g className="constellation-finder__compass" transform={`translate(${CHART_WIDTH - 52}, 44)`}>
            <text y={-6} textAnchor="middle" className="constellation-finder__compass-label">
              N
            </text>
            <line x1={0} y1={0} x2={0} y2={-20} stroke="#9aa8c4" strokeWidth={1.5} />
            <text x={-16} y={3} textAnchor="middle" className="constellation-finder__compass-label">
              E
            </text>
            <text x={16} y={3} textAnchor="middle" className="constellation-finder__compass-label">
              W
            </text>
            <polygon points="0,-24 -3.5,-14 3.5,-14" fill="#9aa8c4" />
          </g>

          <text x={14} y={CHART_HEIGHT - 10} className="constellation-finder__footnote">
            Finder chart · ~35° × 28° · numbered hops: Algol → M34 → Almach
          </text>
        </svg>
      </div>

      <div className="constellation-finder__sidebar">
        <h3 className="constellation-finder__heading">How to find it</h3>
        <ol className="constellation-finder__steps">
          <li>
            Locate <strong>Cassiopeia&apos;s W</strong> high in the north — five bright stars in a zigzag.
          </li>
          <li>
            Star-hop southeast to the <strong>Double Cluster</strong> (χ Per), then continue toward{' '}
            <strong>Algol</strong>.
          </li>
          <li>
            From Algol, sweep west to <strong>M34</strong> — halfway along the line to{' '}
            <strong>Almach</strong> at the foot of Andromeda.
          </li>
        </ol>
        <p>
          Under dark skies M34 is a faint fuzzy patch; binoculars resolve individual stars. The dashed circle
          on the chart shows its true ~35′ diameter.
        </p>
        {hover && (
          <div className="constellation-finder__tooltip" aria-live="polite">
            <strong>{hover.name}</strong>
            {hover.constellation && <span> · {hover.constellation}</span>}
            <br />
            RA {hover.ra.toFixed(2)}° · Dec +{hover.dec.toFixed(2)}° · mag {hover.mag.toFixed(1)}
            {hover.note && <p>{hover.note}</p>}
          </div>
        )}
        {!hover && (
          <p className="constellation-finder__hint">Hover or focus a star on the chart for details.</p>
        )}
      </div>
    </div>
  );
}
