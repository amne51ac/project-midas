/** Named stars and deep-sky landmarks for Credence Atlas (J2000). */

export type AtlasReferenceKind = 'star' | 'galaxy' | 'nebula' | 'cluster';

export interface AtlasReferenceObject {
  id: string;
  name: string;
  ra: number;
  dec: number;
  /** Visual magnitude (approximate for extended DSOs). */
  mag: number;
  constellation: string;
  kind: AtlasReferenceKind;
  note?: string;
  label?: boolean;
}

export const ATLAS_REFERENCE_OBJECTS: AtlasReferenceObject[] = [
  // —— Bright stars (north / equatorial) ——
  { id: 'sirius', name: 'Sirius (α CMa)', ra: 101.287, dec: -16.716, mag: -1.5, constellation: 'Canis Major', kind: 'star', label: true },
  { id: 'canopus', name: 'Canopus (α Car)', ra: 95.988, dec: -52.696, mag: -0.7, constellation: 'Carina', kind: 'star', label: true },
  { id: 'arcturus', name: 'Arcturus (α Boo)', ra: 213.915, dec: 19.182, mag: -0.1, constellation: 'Boötes', kind: 'star', label: true },
  { id: 'vega', name: 'Vega (α Lyr)', ra: 279.235, dec: 38.784, mag: 0.0, constellation: 'Lyra', kind: 'star', label: true },
  { id: 'capella', name: 'Capella (α Aur)', ra: 79.172, dec: 45.998, mag: 0.1, constellation: 'Auriga', kind: 'star', label: true },
  { id: 'rigel', name: 'Rigel (β Ori)', ra: 78.634, dec: -8.202, mag: 0.1, constellation: 'Orion', kind: 'star', label: true },
  { id: 'procyon', name: 'Procyon (α CMi)', ra: 114.825, dec: 5.225, mag: 0.4, constellation: 'Canis Minor', kind: 'star', label: true },
  { id: 'betelgeuse', name: 'Betelgeuse (α Ori)', ra: 88.793, dec: 7.407, mag: 0.5, constellation: 'Orion', kind: 'star', label: true },
  { id: 'achernar', name: 'Achernar (α Eri)', ra: 24.428, dec: -57.237, mag: 0.5, constellation: 'Eridanus', kind: 'star', label: true },
  { id: 'hadar', name: 'Hadar (β Cen)', ra: 210.956, dec: -60.373, mag: 0.6, constellation: 'Centaurus', kind: 'star', label: true },
  { id: 'altair', name: 'Altair (α Aql)', ra: 297.696, dec: 8.868, mag: 0.8, constellation: 'Aquila', kind: 'star', label: true },
  { id: 'acrux', name: 'Acrux (α Cru)', ra: 186.65, dec: -63.1, mag: 0.8, constellation: 'Crux', kind: 'star', label: true },
  { id: 'aldebaran', name: 'Aldebaran (α Tau)', ra: 68.98, dec: 16.509, mag: 0.9, constellation: 'Taurus', kind: 'star', label: true, note: 'Hyades anchor' },
  { id: 'spica', name: 'Spica (α Vir)', ra: 201.298, dec: -11.161, mag: 1.0, constellation: 'Virgo', kind: 'star', label: true },
  { id: 'antares', name: 'Antares (α Sco)', ra: 247.352, dec: -26.432, mag: 1.0, constellation: 'Scorpius', kind: 'star', label: true },
  { id: 'pollux', name: 'Pollux (β Gem)', ra: 116.329, dec: 28.026, mag: 1.1, constellation: 'Gemini', kind: 'star', label: true },
  { id: 'fomalhaut', name: 'Fomalhaut (α PsA)', ra: 344.413, dec: -29.622, mag: 1.2, constellation: 'Piscis Austrinus', kind: 'star', label: true },
  { id: 'deneb', name: 'Deneb (α Cyg)', ra: 310.358, dec: 45.28, mag: 1.3, constellation: 'Cygnus', kind: 'star', label: true },
  { id: 'mimosa', name: 'Mimosa (β Cru)', ra: 191.93, dec: -59.689, mag: 1.3, constellation: 'Crux', kind: 'star', label: true },
  { id: 'regulus', name: 'Regulus (α Leo)', ra: 152.093, dec: 11.967, mag: 1.4, constellation: 'Leo', kind: 'star', label: true },
  { id: 'adhara', name: 'Adhara (ε CMa)', ra: 104.656, dec: -28.972, mag: 1.5, constellation: 'Canis Major', kind: 'star', label: true },
  { id: 'castor', name: 'Castor (α Gem)', ra: 113.649, dec: 31.888, mag: 1.6, constellation: 'Gemini', kind: 'star', label: true },
  { id: 'gacrux', name: 'Gacrux (γ Cru)', ra: 187.79, dec: -57.11, mag: 1.6, constellation: 'Crux', kind: 'star', label: true },
  { id: 'shaula', name: 'Shaula (λ Sco)', ra: 263.402, dec: -37.104, mag: 1.6, constellation: 'Scorpius', kind: 'star', label: true },
  { id: 'bellatrix', name: 'Bellatrix (γ Ori)', ra: 81.283, dec: 6.35, mag: 1.6, constellation: 'Orion', kind: 'star', label: true },
  { id: 'elnath', name: 'Elnath (β Tau)', ra: 81.573, dec: 28.607, mag: 1.7, constellation: 'Taurus', kind: 'star', label: true },
  { id: 'miaplacidus', name: 'Miaplacidus (β Car)', ra: 138.299, dec: -69.717, mag: 1.7, constellation: 'Carina', kind: 'star', label: true },
  { id: 'alnilam', name: 'Alnilam (ε Ori)', ra: 84.053, dec: -1.202, mag: 1.7, constellation: 'Orion', kind: 'star', label: true },
  { id: 'alnitak', name: 'Alnitak (ζ Ori)', ra: 85.19, dec: -1.943, mag: 1.8, constellation: 'Orion', kind: 'star', label: true },
  { id: 'mirfak', name: 'Mirfak (α Per)', ra: 51.08, dec: 49.86, mag: 1.8, constellation: 'Perseus', kind: 'star', label: true },
  { id: 'dubhe', name: 'Dubhe (α UMa)', ra: 165.93, dec: 61.75, mag: 1.8, constellation: 'Ursa Major', kind: 'star', label: true },
  { id: 'algol', name: 'Algol (β Per)', ra: 47.04, dec: 40.96, mag: 2.1, constellation: 'Perseus', kind: 'star', label: true, note: 'Eclipsing binary' },
  { id: 'saiph', name: 'Saiph (κ Ori)', ra: 86.939, dec: -9.67, mag: 2.1, constellation: 'Orion', kind: 'star', label: true },
  { id: 'polaris', name: 'Polaris (α UMi)', ra: 37.95, dec: 89.26, mag: 2.0, constellation: 'Ursa Minor', kind: 'star', label: true },
  { id: 'mirach', name: 'Mirach (β And)', ra: 17.43, dec: 35.62, mag: 2.1, constellation: 'Andromeda', kind: 'star', label: true },
  { id: 'almach', name: 'Almach (γ And)', ra: 30.97, dec: 42.33, mag: 2.1, constellation: 'Andromeda', kind: 'star', label: true, note: 'Golden-blue double' },
  { id: 'caph', name: 'Caph (β Cas)', ra: 17.24, dec: 59.09, mag: 2.3, constellation: 'Cassiopeia', kind: 'star', label: true },
  { id: 'schedar', name: 'Schedar (α Cas)', ra: 10.13, dec: 56.53, mag: 2.2, constellation: 'Cassiopeia', kind: 'star', label: true },
  { id: 'kochab', name: 'Kochab (β UMi)', ra: 222.68, dec: 74.16, mag: 2.1, constellation: 'Ursa Minor', kind: 'star', label: true },
  { id: 'alioth', name: 'Alioth (ε UMa)', ra: 193.51, dec: 55.96, mag: 1.8, constellation: 'Ursa Major', kind: 'star', label: true },
  { id: 'alkaid', name: 'Alkaid (η UMa)', ra: 206.89, dec: 49.31, mag: 1.9, constellation: 'Ursa Major', kind: 'star', label: true },
  { id: 'deneb-Algiedi', name: 'Deneb Algedi (δ Cap)', ra: 326.76, dec: -16.127, mag: 2.9, constellation: 'Capricornus', kind: 'star', label: true },
  { id: 'hamal', name: 'Hamal (α Ari)', ra: 31.79, dec: 23.46, mag: 2.0, constellation: 'Aries', kind: 'star', label: true },
  { id: 'menkar', name: 'Menkar (α Cet)', ra: 45.57, dec: 4.09, mag: 2.5, constellation: 'Cetus', kind: 'star', label: true },
  { id: 'alpheratz', name: 'Alpheratz (α And)', ra: 2.1, dec: 29.09, mag: 2.1, constellation: 'Andromeda', kind: 'star', label: true },
  { id: 'markab', name: 'Markab (α Peg)', ra: 346.19, dec: 15.21, mag: 2.5, constellation: 'Pegasus', kind: 'star', label: true },
  { id: 'scheat', name: 'Scheat (β Peg)', ra: 345.94, dec: 28.08, mag: 2.4, constellation: 'Pegasus', kind: 'star', label: true },
  { id: 'enif', name: 'Enif (ε Peg)', ra: 326.05, dec: 9.88, mag: 2.4, constellation: 'Pegasus', kind: 'star', label: true },

  // —— Perseus / M34 region (finder chart) ——
  { id: 'gamma-cas', name: 'γ Cas', ra: 14.17, dec: 60.72, mag: 2.5, constellation: 'Cassiopeia', kind: 'star', label: true },
  { id: 'ruchbah', name: 'Ruchbah (δ Cas)', ra: 21.45, dec: 60.23, mag: 2.7, constellation: 'Cassiopeia', kind: 'star', label: true },
  { id: 'double-cluster', name: 'Double Cluster (χ Per)', ra: 34.75, dec: 57.15, mag: 3.7, constellation: 'Perseus', kind: 'cluster', label: true, note: 'NGC 869 & 884' },
  { id: 'm34', name: 'M34 · NGC 1039', ra: 40.675, dec: 42.76, mag: 5.2, constellation: 'Perseus', kind: 'cluster', label: true, note: 'T0 benchmark · ~35′ wide' },
  { id: 'delta-and', name: 'δ And', ra: 30.74, dec: 45.87, mag: 3.3, constellation: 'Andromeda', kind: 'star', label: true },

  // —— T0 benchmark clusters ——
  { id: 'pleiades', name: 'Pleiades (M45)', ra: 56.75, dec: 24.12, mag: 1.6, constellation: 'Taurus', kind: 'cluster', label: true, note: 'T0 benchmark cluster' },
  { id: 'hyades', name: 'Hyades', ra: 66.75, dec: 15.87, mag: 0.5, constellation: 'Taurus', kind: 'cluster', label: true, note: 'T0 benchmark cluster' },
  { id: 'praesepe', name: 'Praesepe (M44)', ra: 130.08, dec: 19.78, mag: 3.7, constellation: 'Cancer', kind: 'cluster', label: true, note: 'T0 benchmark cluster' },
  { id: 'm35', name: 'M35 (NGC 2168)', ra: 92.58, dec: 24.35, mag: 5.1, constellation: 'Gemini', kind: 'cluster', label: true, note: 'T0 benchmark cluster' },
  { id: 'ic2602', name: 'IC 2602 · θ Car', ra: 161.0, dec: -64.4, mag: 1.9, constellation: 'Carina', kind: 'cluster', label: true, note: 'T0 benchmark · Southern Pleiades' },

  // —— Galaxies ——
  { id: 'm31', name: 'Andromeda Galaxy (M31)', ra: 10.685, dec: 41.269, mag: 3.4, constellation: 'Andromeda', kind: 'galaxy', label: true, note: 'Nearest major spiral · ~2.5 Mly' },
  { id: 'm33', name: 'Triangulum Galaxy (M33)', ra: 23.462, dec: 30.66, mag: 5.7, constellation: 'Triangulum', kind: 'galaxy', label: true, note: 'Local Group spiral' },
  { id: 'lmc', name: 'Large Magellanic Cloud', ra: 80.894, dec: -69.756, mag: 0.9, constellation: 'Dorado', kind: 'galaxy', label: true, note: 'Irregular satellite galaxy' },
  { id: 'smc', name: 'Small Magellanic Cloud', ra: 13.186, dec: -72.829, mag: 2.7, constellation: 'Tucana', kind: 'galaxy', label: true, note: 'Irregular satellite galaxy' },
  { id: 'm51', name: 'Whirlpool Galaxy (M51)', ra: 202.47, dec: 47.2, mag: 8.4, constellation: 'Canes Venatici', kind: 'galaxy', label: true, note: 'Face-on spiral with companion' },
  { id: 'm81', name: "Bode's Galaxy (M81)", ra: 148.888, dec: 69.065, mag: 6.9, constellation: 'Ursa Major', kind: 'galaxy', label: true },
  { id: 'm82', name: 'Cigar Galaxy (M82)', ra: 148.968, dec: 69.68, mag: 8.4, constellation: 'Ursa Major', kind: 'galaxy', label: true, note: 'Starburst companion to M81' },
  { id: 'm87', name: 'Virgo A (M87)', ra: 187.706, dec: 12.391, mag: 8.6, constellation: 'Virgo', kind: 'galaxy', label: true, note: 'Central giant elliptical · M87 jet' },
  { id: 'm104', name: 'Sombrero Galaxy (M104)', ra: 189.997, dec: -11.623, mag: 8.0, constellation: 'Virgo', kind: 'galaxy', label: true },
  { id: 'ngc5128', name: 'Centaurus A (NGC 5128)', ra: 201.365, dec: -43.019, mag: 6.8, constellation: 'Centaurus', kind: 'galaxy', label: true, note: 'Radio galaxy · dust lane' },
  { id: 'm64', name: 'Black Eye Galaxy (M64)', ra: 194.18, dec: 21.68, mag: 8.5, constellation: 'Coma Berenices', kind: 'galaxy', label: true },
  { id: 'm101', name: 'Pinwheel Galaxy (M101)', ra: 210.8, dec: 54.35, mag: 7.9, constellation: 'Ursa Major', kind: 'galaxy', label: true },

  // —— Nebulae & notable clusters ——
  { id: 'm42', name: 'Orion Nebula (M42)', ra: 83.822, dec: -5.391, mag: 4.0, constellation: 'Orion', kind: 'nebula', label: true, note: 'Star-forming H II region' },
  { id: 'm43', name: 'De Mairan Nebula (M43)', ra: 83.63, dec: -5.27, mag: 9.0, constellation: 'Orion', kind: 'nebula', label: true },
  { id: 'm1', name: 'Crab Nebula (M1)', ra: 83.633, dec: 22.014, mag: 8.4, constellation: 'Taurus', kind: 'nebula', label: true, note: 'Supernova remnant · SN 1054' },
  { id: 'm8', name: 'Lagoon Nebula (M8)', ra: 270.62, dec: -24.383, mag: 5.8, constellation: 'Sagittarius', kind: 'nebula', label: true },
  { id: 'm20', name: 'Trifid Nebula (M20)', ra: 270.62, dec: -23.03, mag: 6.3, constellation: 'Sagittarius', kind: 'nebula', label: true },
  { id: 'm17', name: 'Omega Nebula (M17)', ra: 275.25, dec: -16.18, mag: 6.0, constellation: 'Sagittarius', kind: 'nebula', label: true },
  { id: 'm16', name: 'Eagle Nebula (M16)', ra: 274.7, dec: -13.8, mag: 6.4, constellation: 'Serpens', kind: 'nebula', label: true, note: 'Pillars of Creation region' },
  { id: 'm57', name: 'Ring Nebula (M57)', ra: 283.4, dec: 33.03, mag: 8.8, constellation: 'Lyra', kind: 'nebula', label: true, note: 'Planetary nebula' },
  { id: 'm27', name: 'Dumbbell Nebula (M27)', ra: 299.9, dec: 22.72, mag: 7.5, constellation: 'Vulpecula', kind: 'nebula', label: true, note: 'Planetary nebula' },
  { id: 'm13', name: 'Hercules Globular (M13)', ra: 250.42, dec: 36.46, mag: 5.8, constellation: 'Hercules', kind: 'cluster', label: true, note: 'Great globular cluster' },
  { id: 'm22', name: 'Sagittarius Globular (M22)', ra: 279.1, dec: -23.9, mag: 5.1, constellation: 'Sagittarius', kind: 'cluster', label: true },
  { id: 'm7', name: 'Ptolemy Cluster (M7)', ra: 268.5, dec: -34.8, mag: 3.3, constellation: 'Scorpius', kind: 'cluster', label: true },
  { id: 'm6', name: 'Butterfly Cluster (M6)', ra: 265.1, dec: -32.2, mag: 4.2, constellation: 'Scorpius', kind: 'cluster', label: true },
  { id: 'm41', name: 'M41', ra: 101.0, dec: -20.7, mag: 4.5, constellation: 'Canis Major', kind: 'cluster', label: true },
  { id: 'm47', name: 'M47', ra: 107.0, dec: -14.5, mag: 4.4, constellation: 'Puppis', kind: 'cluster', label: true },
  { id: 'omega-centauri', name: 'Omega Centauri (NGC 5139)', ra: 201.697, dec: -47.479, mag: 3.7, constellation: 'Centaurus', kind: 'cluster', label: true, note: 'Brightest globular in Milky Way' },
  { id: '47-tuc', name: '47 Tucanae (NGC 104)', ra: 6.0, dec: -72.08, mag: 4.0, constellation: 'Tucana', kind: 'cluster', label: true, note: 'Second-brightest globular' },
  { id: 'm11', name: 'Wild Duck Cluster (M11)', ra: 282.75, dec: -6.27, mag: 5.8, constellation: 'Scutum', kind: 'cluster', label: true },
  { id: 'm92', name: 'M92', ra: 259.28, dec: 43.14, mag: 6.4, constellation: 'Hercules', kind: 'cluster', label: true },
  { id: 'm3', name: 'M3', ra: 205.55, dec: 28.38, mag: 6.2, constellation: 'Canes Venatici', kind: 'cluster', label: true },
  { id: 'm15', name: 'M15', ra: 322.5, dec: 12.17, mag: 6.2, constellation: 'Pegasus', kind: 'cluster', label: true },
  { id: 'm2', name: 'M2', ra: 323.5, dec: -0.82, mag: 6.5, constellation: 'Aquarius', kind: 'cluster', label: true },
  { id: 'm4', name: 'M4', ra: 245.9, dec: -26.53, mag: 5.6, constellation: 'Scorpius', kind: 'cluster', label: true, note: 'Nearest globular cluster' },
  { id: 'm5', name: 'M5', ra: 229.64, dec: 2.08, mag: 5.7, constellation: 'Serpens', kind: 'cluster', label: true },
  { id: 'm31-core', name: 'M110 (companion)', ra: 10.1, dec: 41.68, mag: 8.1, constellation: 'Andromeda', kind: 'galaxy', label: true, note: 'Elliptical satellite of M31' },
];
