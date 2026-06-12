/** Full-sky reference layers for Credence Atlas (J2000). */

import {
  BRIGHT_STARS as FINDER_BRIGHT,
  CONSTELLATION_LINES as FINDER_LINES,
} from './finderChart';

export interface AtlasBrightStar {
  id: string;
  name: string;
  ra: number;
  dec: number;
  mag: number;
  constellation: string;
  note?: string;
  label?: boolean;
}

export interface AtlasConstellation {
  id: string;
  name: string;
  points: [number, number][];
}

const EXTRA_BRIGHT: AtlasBrightStar[] = [
  { id: 'sirius', name: 'Sirius (α CMa)', ra: 101.287, dec: -16.716, mag: -1.5, constellation: 'Canis Major', label: true },
  { id: 'canopus', name: 'Canopus (α Car)', ra: 95.988, dec: -52.696, mag: -0.7, constellation: 'Carina', label: true },
  { id: 'arcturus', name: 'Arcturus (α Boo)', ra: 213.915, dec: 19.182, mag: -0.1, constellation: 'Boötes', label: true },
  { id: 'vega', name: 'Vega (α Lyr)', ra: 279.235, dec: 38.784, mag: 0.0, constellation: 'Lyra', label: true },
  { id: 'capella', name: 'Capella (α Aur)', ra: 79.172, dec: 45.998, mag: 0.1, constellation: 'Auriga', label: true },
  { id: 'rigel', name: 'Rigel (β Ori)', ra: 78.634, dec: -8.202, mag: 0.1, constellation: 'Orion', label: true },
  { id: 'procyon', name: 'Procyon (α CMi)', ra: 114.825, dec: 5.225, mag: 0.4, constellation: 'Canis Minor', label: true },
  { id: 'betelgeuse', name: 'Betelgeuse (α Ori)', ra: 88.793, dec: 7.407, mag: 0.5, constellation: 'Orion', label: true },
  { id: 'aldebaran', name: 'Aldebaran (α Tau)', ra: 68.98, dec: 16.509, mag: 0.9, constellation: 'Taurus', label: true, note: 'Hyades anchor' },
  { id: 'spica', name: 'Spica (α Vir)', ra: 201.298, dec: -11.161, mag: 1.0, constellation: 'Virgo', label: true },
  { id: 'antares', name: 'Antares (α Sco)', ra: 247.352, dec: -26.432, mag: 1.0, constellation: 'Scorpius', label: true },
  { id: 'pollux', name: 'Pollux (β Gem)', ra: 116.329, dec: 28.026, mag: 1.1, constellation: 'Gemini', label: true },
  { id: 'fomalhaut', name: 'Fomalhaut (α PsA)', ra: 344.413, dec: -29.622, mag: 1.2, constellation: 'Piscis Austrinus', label: true },
  { id: 'deneb', name: 'Deneb (α Cyg)', ra: 310.358, dec: 45.280, mag: 1.3, constellation: 'Cygnus', label: true },
  { id: 'regulus', name: 'Regulus (α Leo)', ra: 152.093, dec: 11.967, mag: 1.4, constellation: 'Leo', label: true },
  { id: 'castor', name: 'Castor (α Gem)', ra: 113.649, dec: 31.888, mag: 1.6, constellation: 'Gemini', label: true },
  { id: 'bellatrix', name: 'Bellatrix (γ Ori)', ra: 81.283, dec: 6.35, mag: 1.6, constellation: 'Orion' },
  { id: 'elnath', name: 'Elnath (β Tau)', ra: 81.573, dec: 28.607, mag: 1.7, constellation: 'Taurus' },
  { id: 'alnilam', name: 'Alnilam (ε Ori)', ra: 84.053, dec: -1.202, mag: 1.7, constellation: 'Orion' },
  { id: 'alnitak', name: 'Alnitak (ζ Ori)', ra: 85.190, dec: -1.943, mag: 1.8, constellation: 'Orion' },
  { id: 'saiph', name: 'Saiph (κ Ori)', ra: 86.939, dec: -9.67, mag: 2.1, constellation: 'Orion' },
  { id: 'pleiades', name: 'Pleiades (M45)', ra: 56.75, dec: 24.12, mag: 1.6, constellation: 'Taurus', note: 'T0 benchmark cluster', label: true },
  { id: 'hyades', name: 'Hyades', ra: 66.75, dec: 15.87, mag: 0.5, constellation: 'Taurus', note: 'T0 benchmark cluster', label: true },
  { id: 'praesepe', name: 'Praesepe (M44)', ra: 130.08, dec: 19.78, mag: 3.7, constellation: 'Cancer', note: 'T0 benchmark cluster', label: true },
  { id: 'm35', name: 'M35 (NGC 2168)', ra: 92.58, dec: 24.35, mag: 5.1, constellation: 'Gemini', note: 'T0 benchmark cluster' },
  { id: 'ic2602', name: 'IC 2602 · θ Car', ra: 161.0, dec: -64.4, mag: 1.9, constellation: 'Carina', note: 'T0 benchmark cluster · Southern Pleiades', label: true },
  { id: 'acrux', name: 'Acrux (α Cru)', ra: 186.65, dec: -63.1, mag: 0.8, constellation: 'Crux', label: true },
  { id: 'gacrux', name: 'Gacrux (γ Cru)', ra: 187.79, dec: -57.11, mag: 1.6, constellation: 'Crux' },
  { id: 'hadar', name: 'Hadar (β Cen)', ra: 210.956, dec: -60.373, mag: 0.6, constellation: 'Centaurus', label: true },
  { id: 'aviior', name: 'Avior (ε Car)', ra: 125.628, dec: -59.509, mag: 1.9, constellation: 'Carina' },
  { id: 'miaplacidus', name: 'Miaplacidus (β Car)', ra: 138.299, dec: -69.717, mag: 1.7, constellation: 'Carina' },
];

const EXTRA_CONSTELLATIONS: AtlasConstellation[] = [
  {
    id: 'orion',
    name: 'Orion',
    points: [
      [88.793, 7.407], [81.283, 6.35], [84.053, -1.202], [85.19, -1.943], [78.634, -8.202], [86.939, -9.67], [88.793, 7.407],
    ],
  },
  {
    id: 'taurus',
    name: 'Taurus',
    points: [[68.98, 16.509], [81.573, 28.607], [56.75, 24.12], [66.75, 15.87], [68.98, 16.509]],
  },
  {
    id: 'gemini',
    name: 'Gemini',
    points: [[113.649, 31.888], [116.329, 28.026], [92.58, 24.35], [113.649, 31.888]],
  },
  {
    id: 'cancer',
    name: 'Cancer',
    points: [[130.08, 19.78], [152.093, 11.967], [130.08, 19.78]],
  },
  {
    id: 'leo',
    name: 'Leo',
    points: [[152.093, 11.967], [154.993, 23.775], [168.527, 20.524], [152.093, 11.967]],
  },
  {
    id: 'canis-major',
    name: 'Canis Major',
    points: [[101.287, -16.716], [105.756, -23.833], [95.674, -17.956], [101.287, -16.716]],
  },
  {
    id: 'carina',
    name: 'Carina',
    points: [[95.988, -52.696], [125.628, -59.509], [138.299, -69.717], [161.0, -64.4], [95.988, -52.696]],
  },
  {
    id: 'crux',
    name: 'Crux',
    points: [[186.65, -63.1], [187.79, -57.11], [189.71, -58.75], [186.65, -63.1]],
  },
  {
    id: 'centaurus',
    name: 'Centaurus',
    points: [[210.956, -60.373], [186.65, -63.1], [219.902, -60.837], [210.956, -60.373]],
  },
  {
    id: 'scorpius',
    name: 'Scorpius',
    points: [[247.352, -26.432], [252.166, -34.293], [263.402, -37.104], [266.414, -37.296], [247.352, -26.432]],
  },
  {
    id: 'lyra',
    name: 'Lyra',
    points: [[279.235, 38.784], [281.234, 33.362], [282.52, 36.899], [279.235, 38.784]],
  },
  {
    id: 'cygnus',
    name: 'Cygnus',
    points: [[310.358, 45.28], [299.689, 27.96], [292.68, 33.97], [310.358, 45.28]],
  },
];

const finderBright: AtlasBrightStar[] = FINDER_BRIGHT.map((s) => ({
  id: s.id,
  name: s.name,
  ra: s.ra,
  dec: s.dec,
  mag: s.mag,
  constellation: s.constellation,
  note: s.note,
  label: s.label,
}));

const finderConst: AtlasConstellation[] = FINDER_LINES.map((c) => ({
  id: c.id,
  name: c.id.replace(/-/g, ' '),
  points: c.points,
}));

const byId = new Map<string, AtlasBrightStar>();
[...finderBright, ...EXTRA_BRIGHT].forEach((s) => byId.set(s.id, s));

export const ATLAS_BRIGHT_STARS: AtlasBrightStar[] = [...byId.values()].sort((a, b) => a.mag - b.mag);

const constById = new Map<string, AtlasConstellation>();
[...finderConst, ...EXTRA_CONSTELLATIONS].forEach((c) => constById.set(c.id, c));

export const ATLAS_CONSTELLATIONS: AtlasConstellation[] = [...constById.values()];
