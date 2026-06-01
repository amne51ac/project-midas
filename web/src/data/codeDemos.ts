export interface CodeDemoIO {
  name: string;
  meaning: string;
}

export interface CodeDemo {
  id: string;
  title: string;
  summary: string;
  inputs: CodeDemoIO[];
  outputs: CodeDemoIO[];
  code: string;
}

const M34_DISTANCE_PC = 470;

export const CODE_DEMOS: CodeDemo[] = [
  {
    id: 'distance-modulus',
    title: 'Distance modulus → absolute magnitude',
    summary:
      'Convert apparent magnitude V into absolute magnitude M_V using the cluster distance. Every M34 member shares the same distance modulus because the cluster depth is negligible compared to 470 pc.',
    inputs: [
      { name: 'V', meaning: 'Apparent V magnitude (what the telescope measures)' },
      { name: 'd_pc', meaning: 'Distance to the cluster in parsecs (~470 for M34)' },
    ],
    outputs: [
      { name: 'μ = m − M', meaning: 'Distance modulus (mag) — how much brighter the star would be at 10 pc' },
      { name: 'M_V', meaning: 'Absolute V magnitude (intrinsic brightness)' },
    ],
    code: `import math

# --- inputs ---
V_app = 10.5          # apparent V magnitude (mag)
d_pc = ${M34_DISTANCE_PC}           # cluster distance (parsecs)

# --- calculation ---
# Distance modulus: m - M = 5 log10(d/10 pc)
distance_modulus = 5 * math.log10(d_pc / 10)
M_V = V_app - distance_modulus

# --- outputs ---
print("Inputs")
print(f"  V_app  = {V_app:.2f} mag")
print(f"  d      = {d_pc} pc")
print()
print("Outputs")
print(f"  mu     = {distance_modulus:.2f} mag")
print(f"  M_V    = {M_V:.2f} mag")
print()
print("Interpretation: at 470 pc, a star with V=10.5 is intrinsically")
print(f"as bright as a star with V={M_V:.1f} would be at 10 pc.")
`,
  },
  {
    id: 'color-index',
    title: 'B−V color index',
    summary:
      'The color index B−V compares flux in the blue and visual filters. Smaller (or negative) B−V means a hotter, bluer star. This is the horizontal axis of the Project Midas HR diagram.',
    inputs: [
      { name: 'B', meaning: 'Apparent B-band magnitude' },
      { name: 'V', meaning: 'Apparent V-band magnitude' },
    ],
    outputs: [
      { name: 'B−V', meaning: 'Color index (mag). Typical M34 main-sequence stars: ~0.3–0.9' },
    ],
    code: `# --- inputs ---
B = 10.8   # B magnitude
V = 10.2   # V magnitude

# --- calculation ---
bv = B - V

# --- outputs ---
print("Inputs")
print(f"  B = {B:.2f} mag")
print(f"  V = {V:.2f} mag")
print()
print("Outputs")
print(f"  B-V = {bv:.3f} mag")
print()
if bv < 0.3:
    print("Interpretation: hot / blue main-sequence or turnoff star")
elif bv < 0.8:
    print("Interpretation: solar-type or mid main-sequence color")
else:
    print("Interpretation: cooler, redder star (K/M type or reddened)")
`,
  },
  {
    id: 'parallax-distance',
    title: 'Gaia parallax → distance',
    summary:
      'Gaia measures parallax in milliarcseconds (mas). For nearby clusters, π ≈ 1000/d_pc when π is in mas and d is in parsecs (small-angle approximation). Compare to M34 literature distance ~470 pc (π ≈ 2.1 mas).',
    inputs: [
      { name: 'π', meaning: 'Parallax in mas (Gaia DR3 field: phot_parallax or parallax)' },
    ],
    outputs: [
      { name: 'd_pc', meaning: 'Distance in parsecs' },
      { name: 'μ', meaning: 'Implied distance modulus (mag)' },
    ],
    code: `import math

# --- inputs ---
plx_mas = 2.13   # parallax (milliarcseconds)

# --- calculation ---
d_pc = 1000 / plx_mas
distance_modulus = 5 * math.log10(d_pc / 10)

# --- outputs ---
print("Inputs")
print(f"  parallax = {plx_mas:.2f} mas")
print()
print("Outputs")
print(f"  distance = {d_pc:.0f} pc")
print(f"  mu       = {distance_modulus:.2f} mag")
print()
print("Compare to M34: d ~ 470 pc, pi ~ 2.1 mas, mu ~ 8.4 mag")
`,
  },
  {
    id: 'bv-deviation',
    title: 'B−V deviation from a toy isochrone',
    summary:
      'Project Midas compares each star\'s observed B−V to the B−V predicted by a fitted isochrone at the same absolute magnitude. Large deviations can flag binaries, reddening, or non-members. Here we use a simple linear main sequence instead of the full Yonsei–Yale polynomial.',
    inputs: [
      { name: 'B, V', meaning: 'Photometry for one star' },
      { name: 'd_pc', meaning: 'Cluster distance for converting to M_V' },
    ],
    outputs: [
      { name: 'M_V', meaning: 'Absolute magnitude' },
      { name: 'B−V_obs', meaning: 'Measured color' },
      { name: 'B−V_exp', meaning: 'Expected color on toy main sequence' },
      { name: 'Δ(B−V)', meaning: 'Deviation (mag). Midas stores this as bvdev' },
    ],
    code: `import math

# --- inputs ---
B, V = 10.8, 10.2
d_pc = ${M34_DISTANCE_PC}

# --- derived quantities ---
bv_obs = B - V
M_V = V - 5 * math.log10(d_pc / 10)

# Toy isochrone: expected B-V at this M_V (NOT the real YY fit)
B_V_expected = 0.95 - 0.05 * (M_V - 5)
bv_dev = bv_obs - B_V_expected

# --- outputs ---
print("Inputs")
print(f"  B, V   = {B:.2f}, {V:.2f} mag")
print(f"  d      = {d_pc} pc")
print()
print("Outputs")
print(f"  M_V         = {M_V:.2f} mag")
print(f"  B-V obs     = {bv_obs:.3f} mag")
print(f"  B-V expected= {B_V_expected:.3f} mag")
print(f"  deviation   = {bv_dev:+.3f} mag")
print()
if abs(bv_dev) < 0.05:
    print("Interpretation: consistent with single main-sequence star")
else:
    print("Interpretation: candidate binary, variable, or field star")
`,
  },
  {
    id: 'q-value',
    title: 'Binary Q-value (simplified Midas logic)',
    summary:
      'An unresolved equal-mass binary appears ~0.753 mag brighter than a single star at the same B−V (legacy Midas offset). The Q-value measures where the star falls between the single-star and binary tracks: Q ≈ 0 on the single isochrone, Q ≈ 1 on the binary track.',
    inputs: [
      { name: 'B, V', meaning: 'Photometry' },
      { name: 'd_pc', meaning: 'Distance for M_V' },
      { name: 'ΔM_V', meaning: 'Binary luminosity offset (Midas default ≈ 0.753 mag)' },
    ],
    outputs: [
      { name: 'M_V,obs', meaning: 'Observed absolute magnitude' },
      { name: 'M_V,single', meaning: 'Expected M_V on single-star track at this B−V' },
      { name: 'Q', meaning: '0 = single-like, 1 = binary-like (clamped)' },
    ],
    code: `import math

# --- inputs ---
B, V = 10.5, 10.0
d_pc = ${M34_DISTANCE_PC}
DELTA_MV = 0.753   # equal-mass binary offset used in Midas

# --- derived ---
bv = B - V
mv_obs = V - 5 * math.log10(d_pc / 10)

# Toy inverse relation: M_V expected on single-star track at this B-V
mv_single = 12.0 - 1.15 * bv
Q = (mv_single - mv_obs) / DELTA_MV
Q = max(0.0, min(1.0, Q))

# --- outputs ---
print("Inputs")
print(f"  B, V      = {B:.2f}, {V:.2f} mag")
print(f"  d         = {d_pc} pc")
print(f"  delta M_V = {DELTA_MV} mag (binary offset)")
print()
print("Outputs")
print(f"  B-V           = {bv:.3f} mag")
print(f"  M_V observed  = {mv_obs:.2f} mag")
print(f"  M_V single    = {mv_single:.2f} mag (toy track)")
print(f"  Q             = {Q:.3f}")
print()
if Q < 0.2:
    print("Interpretation: photometry matches single-star isochrone")
elif Q > 0.7:
    print("Interpretation: photometry consistent with unresolved binary")
else:
    print("Interpretation: between tracks — investigate further")
`,
  },
  {
    id: 'binary-offset',
    title: 'Equal-mass binary brightness boost',
    summary:
      'Two equal stars in one unresolved point source deliver twice the flux. In magnitudes, Δm = −2.5 log10(2) ≈ −0.753 mag — the star looks brighter (lower M_V) without changing color much.',
    inputs: [
      { name: 'M_V,single', meaning: 'Absolute magnitude if the system were one star' },
      { name: 'flux ratio', meaning: 'Total flux / single-star flux (2 for equal pair)' },
    ],
    outputs: [
      { name: 'ΔM_V', meaning: 'Brightness offset (mag)' },
      { name: 'M_V,binary', meaning: 'Observed absolute magnitude of the blended system' },
    ],
    code: `import math

# --- inputs ---
M_V_single = 3.5
flux_ratio = 2.0   # two equal stars -> twice the flux

# --- calculation ---
delta_M_V = -2.5 * math.log10(flux_ratio)
M_V_binary = M_V_single + delta_M_V

# --- outputs ---
print("Inputs")
print(f"  M_V (single star) = {M_V_single:.2f} mag")
print(f"  flux ratio        = {flux_ratio:.1f}")
print()
print("Outputs")
print(f"  delta M_V         = {delta_M_V:.3f} mag")
print(f"  M_V (binary)      = {M_V_binary:.2f} mag")
print()
print("Midas uses delta M_V ~ 0.753 as the parallel binary track offset.")
`,
  },
  {
    id: 'proper-motion',
    title: 'Proper-motion membership check',
    summary:
      'Cluster members share bulk space motion, so their proper motions (mas/yr) cluster in RA and Dec. Field stars often have different PM. Jones & Prosser (1996) used this; Gaia now measures it for millions of sources.',
    inputs: [
      { name: 'pmRA*, pmDec', meaning: 'Star proper motion (mas/yr). pmRA* = pmRA × cos(Dec)' },
      { name: 'pm_cluster', meaning: 'Adopted cluster center proper motion' },
    ],
    outputs: [
      { name: 'ΔPM', meaning: 'Proper-motion offset from cluster (mas/yr)' },
      { name: 'membership hint', meaning: 'Small ΔPM → likely member' },
    ],
    code: `import math

# --- inputs (example star vs M34 bulk motion) ---
pmra_star = 1.20    # mas/yr
pmdec_star = -6.50  # mas/yr
pmra_cluster = 1.73
pmdec_cluster = -6.34

# --- calculation ---
d_pmra = pmra_star - pmra_cluster
d_pmdec = pmdec_star - pmdec_cluster
delta_pm = math.sqrt(d_pmra**2 + d_pmdec**2)

# --- outputs ---
print("Inputs")
print(f"  star pmRA, pmDec   = {pmra_star:.2f}, {pmdec_star:.2f} mas/yr")
print(f"  cluster pmRA, pmDec= {pmra_cluster:.2f}, {pmdec_cluster:.2f} mas/yr")
print()
print("Outputs")
print(f"  delta pmRA         = {d_pmra:+.2f} mas/yr")
print(f"  delta pmDec        = {d_pmdec:+.2f} mas/yr")
print(f"  |delta PM|         = {delta_pm:.2f} mas/yr")
print()
if delta_pm < 1.0:
    print("Interpretation: proper motion consistent with M34 membership")
else:
    print("Interpretation: likely field star or distant background object")
`,
  },
  {
    id: 'cluster-size',
    title: 'Angular size → physical diameter',
    summary:
      'M34 spans about 35 arcminutes on the sky. Converting that angle plus the distance gives the physical diameter of the cluster in parsecs — useful for understanding survey footprint and tidal radius comparisons.',
    inputs: [
      { name: 'θ', meaning: 'Angular diameter (arcminutes)' },
      { name: 'd_pc', meaning: 'Distance (parsecs)' },
    ],
    outputs: [
      { name: 'θ_deg', meaning: 'Angle in degrees' },
      { name: 'D_pc', meaning: 'Physical diameter (parsecs)' },
    ],
    code: `import math

# --- inputs ---
diameter_arcmin = 35
d_pc = ${M34_DISTANCE_PC}

# --- calculation ---
theta_deg = diameter_arcmin / 60
theta_rad = math.radians(theta_deg)
diameter_pc = d_pc * theta_rad   # small-angle: D = d * theta

# --- outputs ---
print("Inputs")
print(f"  angular size = {diameter_arcmin} arcmin")
print(f"  distance     = {d_pc} pc")
print()
print("Outputs")
print(f"  angle        = {theta_deg:.3f} deg")
print(f"  diameter     = {diameter_pc:.1f} pc (~{diameter_pc * 3.26:.0f} light-years)")
print()
print("The Midas survey field and SkyView cutouts use a similar ~35' scale.")
`,
  },
];
