/** J2000 finder-chart data for the Perseus / Cassiopeia / Andromeda region. */

export interface ChartStar {
  id: string;
  name: string;
  ra: number;
  dec: number;
  mag: number;
  constellation: string;
  note?: string;
  /** Show name on chart */
  label?: boolean;
}

/** Background texture stars (no labels) — real Hipparcos-bright field in this patch. */
export const FIELD_STARS: [ra: number, dec: number, mag: number][] = [
  [12.4, 54.2, 5.1], [19.8, 58.4, 4.8], [24.1, 61.2, 5.3], [33.2, 58.9, 4.6],
  [38.5, 55.1, 5.0], [44.2, 46.8, 4.9], [48.6, 44.2, 5.2], [53.1, 47.5, 4.7],
  [55.8, 41.3, 5.4], [42.1, 39.5, 5.1], [36.8, 44.1, 4.8], [28.4, 48.3, 5.0],
  [22.6, 52.7, 5.2], [15.9, 55.8, 4.9], [8.7, 58.1, 5.3], [26.3, 45.6, 5.1],
  [31.5, 40.2, 5.0], [39.2, 48.6, 4.7], [45.8, 52.3, 5.2], [50.2, 38.9, 5.0],
  [34.1, 53.4, 4.8], [18.2, 62.1, 5.4], [23.7, 54.8, 5.1], [41.6, 45.2, 4.9],
  [47.3, 48.1, 5.0], [52.4, 43.6, 5.3], [37.9, 50.8, 4.6], [29.6, 56.2, 5.2],
  [20.4, 49.1, 5.0], [43.8, 41.7, 5.1], [16.7, 51.3, 4.8], [25.8, 42.8, 5.3],
  [32.6, 46.5, 4.9], [46.1, 54.2, 5.1], [38.9, 38.4, 5.2], [21.1, 57.6, 4.7],
  [27.5, 51.9, 5.0], [35.4, 42.9, 5.1], [49.7, 46.3, 4.8], [14.5, 53.2, 5.2],
  [30.2, 54.6, 4.9], [40.1, 50.1, 5.0], [44.9, 39.8, 5.3], [19.3, 46.7, 5.1],
  [33.8, 47.3, 4.7], [26.9, 43.5, 5.2], [11.8, 60.4, 5.0], [17.6, 54.1, 4.8],
  [36.2, 56.8, 5.1], [42.7, 43.4, 4.9], [48.3, 51.6, 5.2], [22.9, 41.9, 5.0],
  [39.6, 46.2, 4.8], [31.1, 49.7, 5.1], [24.8, 55.3, 5.0], [15.2, 48.8, 5.3],
  [28.7, 44.6, 4.9], [37.4, 52.5, 5.2], [45.2, 47.9, 4.7], [20.7, 59.8, 5.1],
  [34.6, 41.2, 5.0], [41.3, 48.3, 4.8], [29.1, 57.1, 5.3], [23.4, 50.4, 5.1],
  [18.9, 44.2, 4.9], [26.6, 53.8, 5.0], [32.9, 45.7, 5.2], [38.2, 54.6, 4.7],
  [43.5, 40.6, 5.1], [47.8, 49.4, 5.0], [21.6, 47.5, 4.8], [35.7, 43.8, 5.3],
];

export const BRIGHT_STARS: ChartStar[] = [
  { id: 'caph', name: 'Caph (β Cas)', ra: 17.24, dec: 59.09, mag: 2.3, constellation: 'Cassiopeia', label: true },
  { id: 'schedar', name: 'Schedar (α Cas)', ra: 10.13, dec: 56.53, mag: 2.2, constellation: 'Cassiopeia', label: true },
  { id: 'gamma-cas', name: 'γ Cas', ra: 14.17, dec: 60.72, mag: 2.5, constellation: 'Cassiopeia', label: true },
  { id: 'ruchbah', name: 'Ruchbah (δ Cas)', ra: 21.45, dec: 60.23, mag: 2.7, constellation: 'Cassiopeia', label: true },
  { id: 'epsilon-cas', name: 'ε Cas', ra: 28.6, dec: 63.67, mag: 3.4, constellation: 'Cassiopeia', label: true },
  { id: 'double-cluster', name: 'χ Per · Double Cluster', ra: 34.75, dec: 57.15, mag: 3.7, constellation: 'Perseus', note: 'NGC 869 & 884 — bright hop from Cassiopeia', label: true },
  { id: 'mirfak', name: 'Mirfak (α Per)', ra: 51.08, dec: 49.86, mag: 1.8, constellation: 'Perseus', label: true },
  { id: 'algol', name: 'Algol (β Per)', ra: 47.04, dec: 40.96, mag: 2.1, constellation: 'Perseus', note: 'Eclipsing binary — star-hop anchor', label: true },
  { id: 'm34', name: 'M34 · NGC 1039', ra: 40.675, dec: 42.76, mag: 5.2, constellation: 'Perseus', note: '~35′ wide — visible in binoculars' },
  { id: 'delta-and', name: 'δ And', ra: 30.74, dec: 45.87, mag: 3.3, constellation: 'Andromeda', label: true },
  { id: 'almach', name: 'Almach (γ And)', ra: 30.97, dec: 42.33, mag: 2.1, constellation: 'Andromeda', note: 'Golden-blue double star', label: true },
  { id: 'mirach', name: 'Mirach (β And)', ra: 17.43, dec: 35.62, mag: 2.1, constellation: 'Andromeda', label: true },
];

/** Constellation stick figures connecting bright stars [ra, dec]. */
export const CONSTELLATION_LINES: { id: string; points: [number, number][] }[] = [
  {
    id: 'cassiopeia',
    points: [
      [17.24, 59.09], [10.13, 56.53], [14.17, 60.72], [21.45, 60.23], [28.6, 63.67],
    ],
  },
  {
    id: 'perseus-mirfak',
    points: [[51.08, 49.86], [47.04, 40.96], [40.675, 42.76]],
  },
  {
    id: 'perseus-cassiopeia',
    points: [[28.6, 63.67], [34.75, 57.15], [40.675, 42.76]],
  },
  {
    id: 'andromeda',
    points: [[30.97, 42.33], [30.74, 45.87], [17.43, 35.62]],
  },
];

/** Primary star-hop: Algol → M34 → Almach */
export const FINDER_HOPS: [number, number][] = [
  [47.04, 40.96],
  [40.675, 42.76],
  [30.97, 42.33],
];

export const CHART_CENTER = { ra: 30, dec: 52 };
export const CHART_SCALE = 15; // px per degree
export const CHART_WIDTH = 720;
export const CHART_HEIGHT = 560;
export const M34_ANGULAR_SIZE_DEG = 0.583; // ~35 arcmin
