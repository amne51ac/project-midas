/** Yonsei–Yale isochrones (B−V vs Mv) extracted from legacy Midas ISO.csv — solar Z, [Fe/H]=0. */

export interface IsoPoint { mv: number; bv: number; }

export interface AgeIsochrone {
  ageGyr: number;
  label: string;
  shortLabel: string;
  note: string;
  points: IsoPoint[];
}

const RAW: Record<string, IsoPoint[]> = {
  '0.080': [
    { mv: 1.26, bv: -0.042 },
    { mv: 1.39, bv: -0.024 },
    { mv: 1.526, bv: -0.002 },
    { mv: 1.672, bv: 0.027 },
    { mv: 1.834, bv: 0.061 },
    { mv: 2.015, bv: 0.102 },
    { mv: 2.227, bv: 0.15 },
    { mv: 2.474, bv: 0.205 },
    { mv: 2.755, bv: 0.266 },
    { mv: 3.071, bv: 0.328 },
    { mv: 3.423, bv: 0.385 },
    { mv: 3.817, bv: 0.444 },
    { mv: 4.26, bv: 0.518 },
    { mv: 4.733, bv: 0.603 },
    { mv: 5.289, bv: 0.718 },
    { mv: 5.92, bv: 0.848 },
    { mv: 6.637, bv: 0.979 },
    { mv: 7.411, bv: 1.105 },
    { mv: 8.208, bv: 1.23 },
    { mv: 10.148, bv: 1.512 },
  ],
  '0.100': [
    { mv: 1.167, bv: -0.048 },
    { mv: 1.229, bv: -0.041 },
    { mv: 1.35, bv: -0.025 },
    { mv: 1.472, bv: -0.006 },
    { mv: 1.656, bv: 0.028 },
    { mv: 1.783, bv: 0.054 },
    { mv: 1.98, bv: 0.098 },
    { mv: 2.194, bv: 0.145 },
    { mv: 2.42, bv: 0.195 },
    { mv: 2.736, bv: 0.263 },
    { mv: 2.996, bv: 0.314 },
    { mv: 3.393, bv: 0.383 },
    { mv: 3.736, bv: 0.436 },
    { mv: 4.219, bv: 0.515 },
    { mv: 4.337, bv: 0.536 },
    { mv: 5.018, bv: 0.668 },
    { mv: 5.74, bv: 0.815 },
    { mv: 6.528, bv: 0.961 },
    { mv: 7.375, bv: 1.1 },
    { mv: 9.221, bv: 1.381 },
    { mv: 10.32, bv: 1.519 },
  ],
  '0.200': [
    { mv: 0.947, bv: -0.049 },
    { mv: 1.077, bv: -0.037 },
    { mv: 1.263, bv: -0.014 },
    { mv: 1.385, bv: 0.003 },
    { mv: 1.566, bv: 0.033 },
    { mv: 1.751, bv: 0.067 },
    { mv: 1.942, bv: 0.105 },
    { mv: 2.141, bv: 0.146 },
    { mv: 2.418, bv: 0.203 },
    { mv: 2.703, bv: 0.262 },
    { mv: 3.009, bv: 0.321 },
    { mv: 3.369, bv: 0.379 },
    { mv: 3.776, bv: 0.439 },
    { mv: 4.201, bv: 0.508 },
    { mv: 4.627, bv: 0.585 },
    { mv: 4.951, bv: 0.649 },
    { mv: 5.56, bv: 0.778 },
    { mv: 6.214, bv: 0.908 },
    { mv: 6.92, bv: 1.032 },
    { mv: 7.677, bv: 1.15 },
    { mv: 9.385, bv: 1.388 },
    { mv: 11.438, bv: 1.638 },
  ],
  '0.400': [
    { mv: 0.348, bv: -0.019 },
    { mv: 0.117, bv: -0.015 },
    { mv: 0.628, bv: -0.013 },
    { mv: 0.022, bv: -0.011 },
    { mv: 0.84, bv: -0.002 },
    { mv: 1.014, bv: 0.011 },
    { mv: 1.246, bv: 0.034 },
    { mv: 1.391, bv: 0.052 },
    { mv: 1.596, bv: 0.081 },
    { mv: 1.867, bv: 0.123 },
    { mv: 2.068, bv: 0.158 },
    { mv: 2.338, bv: 0.206 },
    { mv: 2.672, bv: 0.268 },
    { mv: 2.953, bv: 0.319 },
    { mv: 3.354, bv: 0.382 },
    { mv: 3.716, bv: 0.433 },
    { mv: 4.178, bv: 0.507 },
    { mv: 4.648, bv: 0.59 },
    { mv: 5.219, bv: 0.707 },
    { mv: 5.707, bv: 0.81 },
    { mv: 6.288, bv: 0.924 },
    { mv: 6.899, bv: 1.031 },
    { mv: 8.244, bv: 1.235 },
    { mv: 9.817, bv: 1.44 },
    { mv: 10.715, bv: 1.541 },
  ],
  '0.600': [
    { mv: 0.937, bv: 0.078 },
    { mv: 0.709, bv: 0.079 },
    { mv: 1.291, bv: 0.095 },
    { mv: 0.471, bv: 0.097 },
    { mv: 1.472, bv: 0.111 },
    { mv: 0.262, bv: 0.138 },
    { mv: 1.716, bv: 0.139 },
    { mv: 2.012, bv: 0.178 },
    { mv: -0.204, bv: 0.178 },
    { mv: 2.293, bv: 0.22 },
    { mv: 2.627, bv: 0.275 },
    { mv: 2.903, bv: 0.319 },
    { mv: 3.284, bv: 0.376 },
    { mv: 3.701, bv: 0.434 },
    { mv: 4.128, bv: 0.501 },
    { mv: 4.649, bv: 0.592 },
    { mv: 5.174, bv: 0.699 },
    { mv: 5.804, bv: 0.831 },
    { mv: 6.19, bv: 0.906 },
    { mv: 7.335, bv: 1.103 },
    { mv: 7.955, bv: 1.197 },
    { mv: 10.126, bv: 1.474 },
    { mv: 10.965, bv: 1.577 },
  ],
  '1.000': [
    { mv: 0.601, bv: 0.166 },
    { mv: 1.604, bv: 0.231 },
    { mv: 1.849, bv: 0.236 },
    { mv: 1.31, bv: 0.253 },
    { mv: 2.223, bv: 0.263 },
    { mv: 2.535, bv: 0.296 },
    { mv: 1.046, bv: 0.329 },
    { mv: 2.829, bv: 0.331 },
    { mv: 3.198, bv: 0.377 },
    { mv: 3.659, bv: 0.435 },
    { mv: 4.11, bv: 0.504 },
    { mv: 4.569, bv: 0.581 },
    { mv: 5.171, bv: 0.7 },
    { mv: 5.857, bv: 0.843 },
    { mv: 6.598, bv: 0.981 },
    { mv: 7.434, bv: 1.12 },
    { mv: 8.495, bv: 1.275 },
    { mv: 9.733, bv: 1.437 },
    { mv: 11.204, bv: 1.613 },
  ],
};

function sortByBv(points: IsoPoint[]): IsoPoint[] {
  return [...points].sort((a, b) => a.bv - b.bv);
}

const META: Record<string, { label: string; short: string; note: string }> = {
  '0.080': { label: '80 Myr', short: '80 Myr', note: 'Very young — turnoff above Mv ≈ 1.3' },
  '0.100': { label: '100 Myr', short: '100 Myr', note: 'Pleiades age — high turnoff, narrow MS gap' },
  '0.200': { label: '200 Myr', short: '200 Myr', note: 'M34 best fit — turnoff near Mv ≈ 1' },
  '0.400': { label: '400 Myr', short: '400 Myr', note: 'Hyades-like — turnoff fainter, gap widens' },
  '0.600': { label: '600 Myr', short: '600 Myr', note: 'Mature cluster — only low-mass stars on MS' },
  '1.000': { label: '1 Gyr', short: '1 Gyr', note: 'Old open cluster — turnoff near solar mass' },
};

export const ISOCHRONE_AGES: AgeIsochrone[] = Object.entries(RAW)
  .map(([k, points]) => ({
    ageGyr: parseFloat(k),
    label: META[k].label,
    shortLabel: META[k].short,
    note: META[k].note,
    points: sortByBv(points),
  }))
  .sort((a, b) => a.ageGyr - b.ageGyr);

/** Ages highlighted in the scrolly age-compare step */
export const SCROLLY_COMPARE_AGES = ISOCHRONE_AGES.filter((a) =>
  [0.1, 0.2, 0.4, 0.6].includes(a.ageGyr),
);

export const M34_AGE_GYR = 0.2;

export function turnoffPoint(iso: IsoPoint[]): IsoPoint {
  return iso.reduce((best, p) => (p.mv < best.mv ? p : best), iso[0]);
}
