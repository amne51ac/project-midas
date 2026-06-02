import { homeSectionHref } from '../routing/appRoute';

export interface PhaseExample {
  kind: 'code' | 'command' | 'stats' | 'note';
  label?: string;
  body: string;
  href?: string;
}

export interface PhaseStep {
  id: string;
  title: string;
  /** ISO date when this step was completed */
  completedDate?: string;
  paragraphs: string[];
  examples?: PhaseExample[];
  /** Link to a home chapter section */
  homeHref?: string;
  homeLabel?: string;
}

export interface PhaseWriteup {
  phaseId: string;
  /** Extended intro beyond the one-line roadmap summary */
  overview: string[];
  steps: PhaseStep[];
  /** Key numbers pulled together at the end */
  outcomes?: { label: string; value: string }[];
}

export const PHASE_WRITEUPS: Record<string, PhaseWriteup> = {
  'phase-i': {
    phaseId: 'phase-i',
    overview: [
      'Phase I was about making the legacy Midas survey legible again. The original work lived in a Python 2 script, an Excel control workbook, and plate-era CSV exports — none of which were easy to audit or share.',
      'We rebuilt the story on the web, ported the photometric pipeline to Python 3, and proved we could reproduce the published singles/binary counts before touching Gaia or new membership catalogs.',
    ],
    steps: [
      {
        id: 'provenance',
        title: 'Map the legacy data',
        completedDate: '2026-06-01',
        paragraphs: [
          'The starting point was the Midas photometry export (~5,749 field stars with BVR(I) magnitudes), Jones & Prosser (1996) proper-motion membership, and Yonsei–Yale isochrone tables in ISO.csv.',
          'Legacy Midas.py dropped any star with B ≥ 30 (a sentinel for missing B-band data), leaving 3,760 stars — the same count used throughout the website HR diagram. We copied raw files into research/data/raw/ and documented every column in DATA_DICTIONARY.md so downstream joins would not guess at trailing spaces in headers or sentinel values.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Raw inputs',
            body: '5,749 photometry rows → 3,760 after B-band filter · 630 Jones–Prosser members · YY isochrones at 0.08–1.0 Gyr',
          },
          {
            kind: 'note',
            body: 'The Declination column in the CSV header includes a trailing space — the loader checks both spellings so joins do not silently fail.',
          },
        ],
        homeHref: homeSectionHref('data'),
        homeLabel: 'Data chapter',
      },
      {
        id: 'site',
        title: 'Build the scrolly site',
        completedDate: '2026-05-31',
        paragraphs: [
          'We wanted the science to be explorable, not buried in a README. The main site walks from cluster history through the HR diagram, catalog overlays, method comparison, runnable code, and the project roadmap.',
          'The HR scrolly section pins a live diagram while prose explains distance modulus, isochrone fitting, and the binary track offset. A six-layer catalog explorer lets you toggle Midas, Gaia, Cantat-Gaudin, Malofeeva, WOCS, and Jones–Prosser on the same field — groundwork for Phase II even though Phase I focused on Midas-only views.',
        ],
        examples: [
          {
            kind: 'note',
            label: 'Stack',
            body: 'Vite + React, D3 for charts, sticky scrolly layout with mobile-safe nav and reduced-motion fallbacks.',
          },
        ],
        homeHref: homeSectionHref('science'),
        homeLabel: 'Science chapter',
      },
      {
        id: 'isochrones',
        title: 'Repair the isochrone tables',
        completedDate: '2026-05-31',
        paragraphs: [
          'The legacy ISO.csv mixed age blocks with formatting quirks that broke naive parsers. build_isochrones.py extracts clean age tracks for the web HR diagram at 0.08, 0.1, 0.15, 0.2, 0.25, 0.5, and 1.0 Gyr.',
          'Analysis defaults to 0.2 Gyr (200 Myr), matching the original Midas.py choice for M34. The isochrone layer on the site is the same data the pipeline uses to compute expected B−V on the single-star and binary tracks.',
        ],
        examples: [
          {
            kind: 'command',
            label: 'Regenerate web isochrones',
            body: 'python scripts/build_isochrones.py',
          },
        ],
        homeHref: homeSectionHref('science'),
        homeLabel: 'HR diagram',
      },
      {
        id: 'py3-port',
        title: 'Port Midas.py to Python 3',
        completedDate: '2026-06-01',
        paragraphs: [
          'The core pipeline lives in research/midas/: load photometry, fit 11th-degree polynomials to the 0.2 Gyr isochrone, compute absolute magnitude at d = 470 pc, and measure B−V deviation from both the single-star and binary tracks.',
          'Jones–Prosser mates are found by position and ΔV cuts (sep < 5.2″, |ΔV| < 0.457 mag). The Q-value flags equal-mass binary candidates: how far the star sits below the single-star isochrone, normalized by the binary track offset (0.753 mag in the legacy path).',
        ],
        examples: [
          {
            kind: 'code',
            label: 'Pipeline outputs (per star)',
            body: `mv   = V − 5 log₁₀(470/10)          # absolute V
xbv  = poly(Mv) on 0.2 Gyr isochrone  # expected B−V, single star
bvdev = (B−V) − xbv                   # single-star deviation
Q    = (Mv_iso − Mv_obs) / 0.753      # binary heuristic`,
          },
          {
            kind: 'command',
            label: 'Run the pipeline',
            body: 'python scripts/run_midas_pipeline.py\n# → data/processed/midas_pipeline.csv',
          },
        ],
        homeHref: homeSectionHref('code'),
        homeLabel: 'Code chapter',
      },
      {
        id: 'excel-regression',
        title: 'Reproduce Excel Control counts',
        completedDate: '2026-06-01',
        paragraphs: [
          'The published Midas counts — 187 accepted singles and 171 binaries — come from the Excel workbook House of Binary Midas Madness.xlsx, not directly from Midas.py. The spreadsheet uses a fixed 6th-degree polynomial for expected B−V, a circular spatial filter around the cluster center, and slightly different classification thresholds.',
          'midas/excel.py implements that Control-sheet logic exactly. reproduce_excel_counts.py is the regression gate: it must print 187 / 171 before we trust any pipeline change. The legacy Python path (11th-degree ISO fit + Q-value) produces different singles/binary splits — both are documented so Phase III validation knows which definition it is testing against.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Excel Control parameters',
            body: 'd = 470 pc · |Δ(B−V)| < 0.05 singles · |Δ(B−V)| < 0.10 binaries · ΔMv = 0.732 mag binary shift · 37′ diameter field',
          },
          {
            kind: 'command',
            label: 'Regression test',
            body: 'python scripts/reproduce_excel_counts.py\n# PASS — Excel counts reproduced.',
          },
          {
            kind: 'code',
            label: 'Expected B−V (Excel polynomial)',
            body: 'expected_bv(Mv) = np.polyval(EXCEL_BV_POLY, Mv)\n# degree-6 coefficients from Control sheet column AI',
          },
        ],
        homeHref: homeSectionHref('compare'),
        homeLabel: 'Compare chapter',
      },
      {
        id: 'pyodide',
        title: 'Runnable arithmetic in the browser',
        completedDate: '2026-05-31',
        paragraphs: [
          'Eight Pyodide demos on the Code chapter let readers run the same formulas as the pipeline — distance modulus, isochrone interpolation, Q-value, proper-motion separation — without installing Python.',
          'Each demo is a self-contained accordion with syntax highlighting and editable inputs. They mirror research/scripts/abs_mag.py and the midas package so the website and CLI stay aligned.',
        ],
        examples: [
          {
            kind: 'note',
            label: 'Demos',
            body: 'Distance modulus · B−V deviation · Binary track offset · Q-value · Proper-motion check · Isochrone age pick · Spatial filter · Membership mate search',
          },
        ],
        homeHref: homeSectionHref('code'),
        homeLabel: 'Try the arithmetic',
      },
      {
        id: 'data-dict',
        title: 'Document every column',
        completedDate: '2026-06-01',
        paragraphs: [
          'DATA_DICTIONARY.md covers raw CSV columns, pipeline outputs (midas_pipeline.csv), and the join schema Phase II would populate. Each field notes type, units, sentinel values, and which script produces it.',
          'Together with research/README.md and midas.paths, a new collaborator can locate files, run the pipeline, and interpret outputs without opening the legacy Excel workbook first.',
        ],
        examples: [
          {
            kind: 'note',
            body: 'Key pipeline columns: midas_id, mv, bv, xbv, bvdev, Q, jp_mate, jp_mem — plus excel_single / excel_binary flags after cross_match.py (Phase II).',
          },
        ],
      },
      {
        id: 'ci',
        title: 'Ship with CI',
        completedDate: '2026-05-31',
        paragraphs: [
          'GitHub Actions builds and deploys the static site on every push to main. The research tree has its own requirements.txt (numpy, scipy, astropy) separate from the web bundle.',
          'For GitHub Pages, set VITE_BASE_PATH to the repository name so asset paths resolve under the project URL.',
        ],
        examples: [
          {
            kind: 'command',
            label: 'Local build',
            body: 'cd web && npm run build',
          },
        ],
        homeHref: homeSectionHref('tools'),
        homeLabel: 'Tools inventory',
      },
    ],
    outcomes: [
      { label: 'Photometry sample', value: '3,760 stars' },
      { label: 'Excel singles / binaries', value: '187 / 171' },
      { label: 'Browser Python demos', value: '8' },
      { label: 'Pipeline package', value: 'research/midas/' },
      { label: 'Phase completed', value: '1 Jun 2026' },
    ],
  },
  'phase-ii': {
    phaseId: 'phase-ii',
    overview: [
      'Phase II connected the legacy Midas photometry to the modern sky. Every Midas star now has a Gaia DR3 match where possible, published membership and binary catalogs on the same row, and de-reddened colors for fair comparison to isochrones.',
      'The join table is the spine: cross_match.py builds m34_join.csv once, build_web_sample.py and build_web_catalogs.py push it to the static site, and the HR diagram and data explorer read membership, reddening, and catalog flags without re-running Astropy in the browser.',
    ],
    steps: [
      {
        id: 'gaia-field',
        title: 'Export the Gaia DR3 field',
        completedDate: '2026-06-01',
        paragraphs: [
          'Before we could attach astrometry to Midas IDs, we needed a local Gaia cone around M34. gaia_cone.py queries DR3 within 0.5° of the cluster center and writes gaia_m34.csv — 15,211 sources with positions, parallax, proper motion, G magnitude, and RUWE.',
          'The export is intentionally wider than the Midas plate footprint so cross-matching has neighbors to choose from and the data explorer can show Gaia as its own layer without another network call at build time.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Gaia field',
            body: '15,211 DR3 sources · 0.5° cone · M34 center (40.675°, +42.76°)',
          },
          {
            kind: 'command',
            label: 'Regenerate Gaia export',
            body: 'python scripts/gaia_cone.py\n# → data/processed/gaia_m34.csv',
          },
        ],
        homeHref: homeSectionHref('data'),
        homeLabel: 'Data explorer',
      },
      {
        id: 'cantat',
        title: 'Ingest Cantat-Gaudin UPMASK membership',
        completedDate: '2026-06-01',
        paragraphs: [
          'Jones–Prosser (1996) proper-motion membership was the legacy gate, but Cantat-Gaudin et al. (2020) provides probabilistic UPMASK membership for 555 M34 stars from Gaia DR2 astrometry — a better baseline for Phase III validation.',
          'We pulled J/A+A/640/A1 from VizieR and store cg_proba on every Midas row in the join table. At the default threshold P ≥ 0.7, 263 Midas photometry stars are high-confidence members; the HR diagram and data explorer can filter to that subset.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Cantat-Gaudin overlap',
            body: '555 catalog stars · 263 Midas matches at P ≥ 0.7 · cg_proba + cg_member on m34_join.csv',
          },
          {
            kind: 'code',
            label: 'Membership flag',
            body: 'cg_member = 1 if cg_proba ≥ 0.7 else 0\n# midas/membership.py — DEFAULT_CG_MEMBER_THRESHOLD',
          },
        ],
        homeHref: homeSectionHref('data'),
        homeLabel: 'Toggle CG layer',
      },
      {
        id: 'malofeeva',
        title: 'Ingest Malofeeva IR binary sample',
        completedDate: '2026-06-01',
        paragraphs: [
          'Malofeeva et al. (2023) publish 553 M34 stars with WISE color cuts that flag likely IR-excess / binary candidates — independent of the Midas isochrone Q-value.',
          'VizieR table J/AJ/165/45 is ingested with W2−BP and H−W1 color indices where available. 248 targets overlap Midas photometry in m34_join.csv; the data explorer highlights them in a separate layer so readers can compare photometric and IR diagnostics side by side.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Malofeeva overlap',
            body: '553 catalog stars · 248 Midas matches · malofeeva flag + WISE colors on join row',
          },
        ],
        homeHref: homeSectionHref('compare'),
        homeLabel: 'Compare chapter',
      },
      {
        id: 'wocs',
        title: 'Ingest WOCS RV + rotation targets',
        completedDate: '2026-06-01',
        paragraphs: [
          'The WOCS survey (Meibom et al. 2011) provides ground-truth radial-velocity and rotation-period measurements for M34 — the gold standard for validating photometric binary picks in Phase III.',
          'midas/wocs.py loads 120 VizieR targets from J/ApJ/733/115/table2 with sequence IDs, Prot, RV, and RV membership probability. Positional matching finds 118 Midas photometry counterparts; Seq 2 and 89 fall outside the B-band sample (B ≥ 30 sentinel) and correctly remain unmatched.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'WOCS ingest',
            body: '120 VizieR targets · 118 Midas matches · wocs_seq, wocs_prot, wocs_rv on join row',
          },
          {
            kind: 'command',
            label: 'Verify WOCS matching',
            body: 'python scripts/verify_wocs_ingest.py\n# 118/120 expected (Seq 2 & 89 outside sample)',
          },
        ],
        homeHref: homeSectionHref('data'),
        homeLabel: 'Toggle WOCS layer',
      },
      {
        id: 'cross-match',
        title: 'Build the unified join table',
        completedDate: '2026-06-01',
        paragraphs: [
          'cross_match.py is the single entry point: load 3,760 Midas stars, match each to Gaia DR3 with Astropy SkyCoord (default 1.5″), then attach Cantat-Gaudin, Malofeeva, WOCS, and Jones–Prosser flags plus Excel Control singles/binary classification from midas/excel.py.',
          'The output m34_join.csv has one row per Midas star with 37 columns documented in DATA_DICTIONARY.md. Gaia match rate is 99.4% (3,738 / 3,760); the 22 unmatched stars are typically faint or have poor astrometry at the cluster edge.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Join coverage',
            body: '3,760 Midas rows · 3,738 Gaia (99.4%) · 263 CG · 248 Malofeeva · 118 WOCS · 222 Jones–Prosser',
          },
          {
            kind: 'command',
            label: 'Rebuild join table',
            body: 'python scripts/cross_match.py\n# → data/processed/m34_join.csv',
          },
          {
            kind: 'note',
            body: 'Excel singles/binaries (187 / 171) are recomputed on each run so the join stays aligned with the Phase I regression gate.',
          },
        ],
        homeHref: homeSectionHref('compare'),
        homeLabel: 'Joining the layers',
      },
      {
        id: 'membership',
        title: 'Wire membership into the site',
        completedDate: '2026-06-01',
        paragraphs: [
          'Probabilistic membership is useless if it only lives in a CSV on disk. build_web_sample.py reads m34_join.csv and emits m34_sample.json with cgProba, cgMember, gaiaId, and catalog flags on each HR point. build_web_catalogs.py does the same for the six-layer data explorer.',
          'On the Science chapter, HR diagram toggles let readers switch to de-reddened colors and restrict the plot to Cantat-Gaudin members. DataExplorer tooltips show membership probability and WOCS/Malofeeva flags when hovering matched stars.',
        ],
        examples: [
          {
            kind: 'command',
            label: 'Push join data to the web bundle',
            body: 'python scripts/build_web_sample.py\npython scripts/build_web_catalogs.py',
          },
          {
            kind: 'note',
            label: 'Site filters',
            body: 'De-reddened (E(B−V)=0.07) · Cantat-Gaudin members only (P≥0.7) · six catalog layers on the data explorer',
          },
        ],
        homeHref: homeSectionHref('science'),
        homeLabel: 'HR diagram filters',
      },
      {
        id: 'reddening',
        title: 'Apply uniform reddening corrections',
        completedDate: '2026-06-01',
        paragraphs: [
          'M34 sits at low Galactic latitude with modest but non-zero reddening. midas/reddening.py applies a uniform E(B−V) = 0.07 (R_V = 3.1) across the field — literature value for now; a 3D dust map can replace this in a later pass.',
          'cross_match.py writes ebv, bv0, and mv0 on every join row. The HR toggles use bv0/mv0 when de-reddening is enabled; run_midas_pipeline.py accepts an optional --ebv flag so CLI and join table stay consistent.',
        ],
        examples: [
          {
            kind: 'code',
            label: 'De-reddening',
            body: `bv0 = (B−V) − E(B−V)              # intrinsic color
V0  = V − R_V · E(B−V)              # de-reddened apparent V
mv0 = V0 − 5 log₁₀(470/10)          # absolute V, corrected`,
          },
          {
            kind: 'stats',
            label: 'Defaults',
            body: 'E(B−V) = 0.07 · R_V = 3.1 · uniform across field',
          },
        ],
        homeHref: homeSectionHref('science'),
        homeLabel: 'De-reddened HR view',
      },
      {
        id: 'parsec',
        title: 'Add PARSEC isochrone comparison',
        completedDate: '2026-06-01',
        paragraphs: [
          'Phase I relied on Yonsei–Yale isochrones from the legacy ISO.csv. For modern model comparison we fetch PARSEC v1.2S tracks from the Padova CMD 3.9 web service at the same ages as the YY grid (80 Myr–1 Gyr).',
          'fetch_parsec_isochrones.py caches raw tables; build_parsec_isochrones.py emits web/src/data/parsecIsochrones.ts. The isochrone gallery and HR scrolly steps overlay dashed cyan PARSEC curves beside solid YY tracks, with turnoff statistics on each age card.',
        ],
        examples: [
          {
            kind: 'command',
            label: 'Fetch and build PARSEC layer',
            body: 'python scripts/fetch_parsec_isochrones.py\npython scripts/build_parsec_isochrones.py',
          },
          {
            kind: 'note',
            label: 'On the site',
            body: 'Isochrone gallery: PARSEC toggle per age card · HR scrolly: YY vs PARSEC on age-compare and age-fit steps',
          },
        ],
        homeHref: homeSectionHref('science'),
        homeLabel: 'Isochrone gallery',
      },
    ],
    outcomes: [
      { label: 'Gaia match rate', value: '99.4% (3,738 / 3,760)' },
      { label: 'CG members (P≥0.7)', value: '263' },
      { label: 'Malofeeva / WOCS overlap', value: '248 / 118' },
      { label: 'Join table columns', value: '37 in m34_join.csv' },
      { label: 'Phase completed', value: '1 Jun 2026' },
    ],
  },
  'phase-iii': {
    phaseId: 'phase-iii',
    overview: [
      'Phase III asks whether the legacy Midas Q-value heuristic recovers binaries that independent surveys already flagged — IR-color cuts (Malofeeva), WOCS radial-velocity variability, and Gaia astrometric quality (RUWE).',
      'All comparisons run on CG members (P ≥ 0.7) with Q values from the Python 3 pipeline at E(B−V) = 0.07. Results land in validation_summary.json and the q_threshold_calibration notebook.',
    ],
    steps: [
      {
        id: 'malofeeva',
        title: 'Q vs Malofeeva IR binaries',
        paragraphs: [
          'Malofeeva et al. (2023) flags 248 Midas overlaps via Gaia+WISE pseudocolors — independent of the isochrone track offset. Among 263 Cantat-Gaudin members, 242 carry the Malofeeva flag; we treat those as positive class for a first completeness check.',
          'Default legacy cut (0 < Q ≤ 1, excluding |Δ(B−V)| < 0.05 singles) yields high precision (0.92) but low recall (0.19) vs Malofeeva — most IR-flagged stars sit above the binary track in B−V space without a high Q-value.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'CG members · Malofeeva truth',
            body: 'N=263 · TP=47 FP=4 · Precision=0.92 · Recall=0.19 · F1=0.32',
          },
          {
            kind: 'command',
            label: 'Run',
            body: 'python scripts/validate_phase3.py --only malofeeva',
          },
        ],
        homeHref: homeSectionHref('compare'),
        homeLabel: 'Compare chapter',
      },
      {
        id: 'wocs',
        title: 'Q vs WOCS RV variability',
        paragraphs: [
          'WOCS publishes a probability PRV that a star\'s radial velocity is variable — our binary truth uses PRV ≥ 90%. Only 23 of 118 Midas-matched WOCS targets have PRV measurements in the VizieR table; the rest lack RV follow-up.',
          'On that subset the default Q cut finds no PRV-high stars (TP=0) — expected at ~200 Myr where many WOCS binaries are resolved or rotate, not unresolved equal-mass pairs.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'WOCS with PRV',
            body: 'N=23 with PRV · truth PRV≥90% · TP=0 FP=3 TN=20',
          },
          {
            kind: 'command',
            label: 'Verify WOCS ingest',
            body: 'python scripts/verify_wocs_ingest.py',
          },
        ],
        homeHref: homeSectionHref('data'),
        homeLabel: 'WOCS layer',
      },
      {
        id: 'ruwe',
        title: 'Gaia RUWE astrometric screen',
        paragraphs: [
          'Gaia DR3 RUWE > 1.4 flags astrometric solutions inconsistent with a single star — a third binary diagnostic orthogonal to B−V and IR colors.',
          'Among CG members with RUWE, the Q-value picks up 7 of 23 high-RUWE stars (recall 0.30) at the cost of 44 false positives — astrometric and photometric binary channels overlap partially but are not identical.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'RUWE > 1.4 vs Q',
            body: 'N=263 · TP=7 FP=44 · Precision=0.14 · Recall=0.30 · F1=0.19',
          },
        ],
        homeHref: homeSectionHref('data'),
        homeLabel: 'Gaia layer',
      },
      {
        id: 'roc',
        title: 'ROC and magnitude-binned completeness',
        paragraphs: [
          'ROC curves treat Q as a continuous score (higher = more binary-like) against Malofeeva positives. Bootstrap resampling by absolute magnitude bin estimates recall uncertainty — completeness rises toward faint magnitudes (Mv 8–14: recall ≈ 0.37) where unresolved pairs dominate.',
          'Output includes 264 ROC points and per-bin 95% CI on recall for planning Phase IV mass-stratified fractions.',
        ],
        examples: [
          {
            kind: 'command',
            label: 'Full validation report',
            body: 'python scripts/validate_phase3.py --refresh-pipeline --ebv 0.07\n# → data/processed/validation_summary.json',
          },
          {
            kind: 'note',
            label: 'Mv bin recall (Malofeeva)',
            body: 'Mv 0–2: 0.09 · 2–4: 0.14 · 4–6: 0.16 · 6–8: 0.07 · 8–14: 0.37',
          },
        ],
      },
      {
        id: 'calibrate',
        title: 'Q threshold calibration notebook',
        paragraphs: [
          'research/notebooks/q_threshold_calibration.ipynb sweeps (q_low, q_high) bounds and plots ROC + F1 heatmaps. The default (0, 1] interval already maximizes F1 vs Malofeeva among tested grids — tightening q_high below 0.9 only hurts recall.',
          'Next tuning should joint-optimize bvdev_single_max and Q bounds, and compare Excel-binary vs Q paths as separate predictors.',
        ],
        examples: [
          {
            kind: 'command',
            label: 'Threshold grid only',
            body: 'python scripts/validate_phase3.py --only calibrate',
          },
        ],
        homeHref: homeSectionHref('code'),
        homeLabel: 'Code chapter',
      },
      {
        id: 'ir-fetch',
        title: 'Cache 2MASS + AllWISE field photometry',
        paragraphs: [
          'Malofeeva et al. publish pre-selected IR-binary candidates; Phase III also needs a field-wide near-IR cache to build independent color diagrams (W1−W2, J−K, and W2−BP after Gaia cross-match) without relying on their figure-9 table alone.',
          'fetch_ir_photometry.py queries VizieR II/246 (2MASS PSC) and II/328 (AllWISE) in a 0.35° cone around M34. Positional matching finds 2,061 Midas stars with 2MASS and 2,109 with AllWISE within 2″.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Field cache',
            body: '2MASS: 3,383 sources · AllWISE: 6,985 · Midas overlap ≤2″: 2,061 / 2,109',
          },
          {
            kind: 'command',
            label: 'Fetch IR cones',
            body: 'python scripts/fetch_ir_photometry.py --verify',
          },
        ],
        homeHref: homeSectionHref('tools'),
        homeLabel: 'Tools inventory',
      },
    ],
    outcomes: [
      { label: 'Validation module', value: 'research/midas/validation.py' },
      { label: 'Malofeeva F1 (CG)', value: '0.32 @ Q∈(0,1]' },
      { label: '2MASS / AllWISE cache', value: '3,383 / 6,985' },
      { label: 'Midas IR overlap', value: '2,061 / 2,109' },
      { label: 'Phase completed', value: '1 Jun 2026' },
    ],
  },
  'phase-iv': {
    phaseId: 'phase-iv',
    overview: [
      'Phase IV turns the Phase III validation channels into population-level answers: what fraction of Cantat-Gaudin members are binaries, and how does that depend on mass?',
      'The key design choice is deduplication — each Midas star counts once. A star is binary in the union sample if any of five independent channels fires: legacy Q-value, Malofeeva IR colors, Excel Control binaries, WOCS RV variability (PRV ≥ 90%), or Gaia RUWE > 1.4. Channel hit counts are reported separately because they overlap heavily.',
    ],
    steps: [
      {
        id: 'mass-map',
        title: 'Map absolute magnitude to stellar mass',
        paragraphs: [
          'Mass bins need a monotonic Mv → M☉ map. midas/mass.py inverts the Yonsei–Yale 0.2 Gyr isochrone (the same age Midas.py used for M34) so each CG member with a de-reddened Mv lands in a physical mass bin.',
          'Default bins span 0.45–2.6 M☉ in six intervals — wide enough for stable bootstrap counts on N=263 members, narrow enough to see a trend if low-mass stars host fewer equal-mass unresolved pairs.',
        ],
        examples: [
          {
            kind: 'note',
            label: 'Isochrone age',
            body: '0.2 Gyr (200 Myr) · E(B−V)=0.07 · 258 / 263 members with finite mass',
          },
        ],
        homeHref: homeSectionHref('science'),
        homeLabel: 'Isochrone gallery',
      },
      {
        id: 'union',
        title: 'Deduplicated binary union',
        completedDate: '2026-06-01',
        paragraphs: [
          'Among 263 Cantat-Gaudin members (P ≥ 0.7), the union flags 253 as binary — 96.2%. Malofeeva alone accounts for 242 hits because most IR-flagged stars never received a high Q-value; Excel Control adds 83; Q-value adds 51; RUWE adds 23; WOCS PRV adds 0 on the 23 targets with measurements.',
          'This is an upper envelope on “binary or binary-like” rather than a clean spectroscopic fraction — Malofeeva and RUWE probe different physics than unresolved equal-mass pairs. Per-channel fractions and overlap matrices feed the method-comparison write-up.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Channel hits (not exclusive)',
            body: 'Q=51 · Malofeeva=242 · Excel=83 · WOCS PRV=0 · RUWE=23 · Union=253',
          },
          {
            kind: 'command',
            label: 'Run synthesis',
            body: 'python scripts/run_phase4_synthesis.py --ebv 0.07\n# → data/processed/synthesis_summary.json',
          },
        ],
        homeHref: homeSectionHref('compare'),
        homeLabel: 'Compare chapter',
      },
      {
        id: 'fraction-mass',
        title: 'Binary fraction vs. mass',
        completedDate: '2026-06-01',
        paragraphs: [
          'Bootstrap resampling within each mass bin yields 95% confidence intervals on the union fraction. All six bins sit above 92% — the Malofeeva channel dominates every bin, so the mass dependence is flat in this first pass.',
          'Per-channel fractions by mass (also in synthesis_summary.json) show where Q-value and Excel pick up stars Malofeeva misses — the material for the B−V vs Gaia+IR comparison.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Union f(binary) by M☉',
            body: '0.45–0.65: 0.99 · 0.65–0.85: 0.96 · 0.85–1.05: 0.94 · 1.05–1.25: 0.97 · 1.25–1.55: 0.95 · 1.55–2.6: 0.92',
          },
          {
            kind: 'note',
            label: 'Interpretation',
            body: 'Flat mass trend reflects Malofeeva completeness, not a measured MF — tighten with channel-exclusive fractions and WOCS RV follow-up.',
          },
        ],
      },
      {
        id: 'ir-merge',
        title: 'Merge 2MASS + AllWISE into join table',
        paragraphs: [
          'Independent IR colors (J−K, W1−W2, W2−BP) need photometry on the same Midas rows as the B−V pipeline. merge_ir_photometry.py cross-matches the Phase III field caches to m34_join.csv at ≤2″ and writes m34_join_ir.csv with Gaia BP for pseudocolor diagrams.',
          '2,089 stars now carry W2−BP — the same color space Malofeeva used — so we can plot Midas Q picks and Malofeeva flags on identical axes without their pre-selected sample table.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'IR cross-match',
            body: '2MASS: 2,061 · AllWISE: 2,109 · W2−BP: 2,089 of 3,760 Midas stars',
          },
          {
            kind: 'command',
            label: 'Rebuild IR join',
            body: 'python scripts/fetch_ir_photometry.py --verify\npython scripts/merge_ir_photometry.py\n# → data/processed/m34_join_ir.csv',
          },
        ],
        homeHref: homeSectionHref('data'),
        homeLabel: 'Data explorer',
      },
      {
        id: 'method-compare',
        title: 'Methods comparison (B−V vs Gaia+IR)',
        completedDate: '2026-06-01',
        paragraphs: [
          'The Compare chapter now shows channel hit counts, exclusive Q/Malofeeva partitions, mass-binned fractions, and an interactive W2−BP vs de-reddened B−V diagram on 223 CG members with AllWISE+Gaia BP photometry.',
          'Malofeeva-only stars dominate the IR-excess region; Q-only picks are sparse (4 in the full CG sample, 3 with IR on the diagram). Dual-flag stars (Q ∩ Malofeeva) form a visible overlap wedge — the photometric track offset and IR pseudocolor channels are partially correlated but far from identical.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Diagram layers (223 with W2−BP)',
            body: 'Mal only: 166 · Q∩Mal: 45 · Q only: 1 · Excel: 3 · None: 7',
          },
          {
            kind: 'command',
            label: 'Regenerate web exports',
            body: 'python scripts/merge_ir_photometry.py\npython scripts/build_web_synthesis.py\n# → synthesisSummary.json + methodCompareDiagram.json',
          },
        ],
        homeHref: homeSectionHref('compare'),
        homeLabel: 'Compare chapter',
      },
      {
        id: 'wd-check',
        title: 'Rubin et al. white dwarf astrometry',
        completedDate: '2026-06-01',
        paragraphs: [
          'Rubin et al. (2008) selected 44 LAWDS white dwarf candidates via UBV imaging; 17 were confirmed spectroscopically (mostly DA). Five DA WDs sit at the cluster distance modulus — the anchors for their initial–final mass relation plot.',
          'We ingest Table 2 coordinates and cross-match to our Gaia DR3 field export. At V ≈ 19–21 many candidates lack Gaia matches or have unreliable parallaxes; only LAWDS 15 and 17 show partial PM agreement with the Cantat-Gaudin member locus. Rubin photometric membership remains the strongest constraint until DR4 or dedicated PM follow-up.',
        ],
        examples: [
          {
            kind: 'stats',
            label: 'Gaia DR3 cross-match',
            body: '44 candidates · 22 Gaia matches · 0 clean π+PM cluster hits · 5 paper members',
          },
          {
            kind: 'command',
            label: 'Run WD check',
            body: 'python scripts/fetch_rubin_wd.py\npython scripts/validate_wd_check.py\npython scripts/build_web_wd_check.py',
          },
        ],
        homeHref: homeSectionHref('compare'),
        homeLabel: 'WD table on Compare chapter',
      },
      {
        id: 'release',
        title: 'Public data release',
        completedDate: '2026-06-01',
        paragraphs: [
          'Phase IV closes with a reproducible package: REPRODUCTION.md documents every script stage, run_reproduction.py orchestrates core → validation → synthesis → web exports, and build_web_all.py refreshes the JSON the public site reads.',
          'Processed CSVs remain gitignored (regenerate locally); web/src/data/ holds portable summaries — synthesis overlap, method-compare diagram points, WD check table, HR sample, and catalog layers. CITATION.cff provides a standard citation block for the repository.',
        ],
        examples: [
          {
            kind: 'command',
            label: 'Full reproduction',
            body: 'cd research && source .venv/bin/activate\npython scripts/run_reproduction.py --stage all\ncd ../web && npm run build',
          },
          {
            kind: 'note',
            label: 'Web-only refresh',
            body: 'python scripts/build_web_all.py  # after processed/ tables exist',
          },
        ],
        homeHref: homeSectionHref('tools'),
        homeLabel: 'Tools chapter — data release',
      },
    ],
    outcomes: [
      { label: 'Synthesis module', value: 'research/midas/synthesis.py' },
      { label: 'Union f(binary)', value: '96.2% (253 / 263 CG)' },
      { label: 'Method compare UI', value: 'Compare ch. — overlap + W2−BP' },
      { label: 'WD check', value: '44 LAWDS · 22 Gaia DR3' },
      { label: 'Reproduction guide', value: 'research/REPRODUCTION.md' },
      { label: 'Phase completed', value: '1 Jun 2026' },
    ],
  },
};

export function getPhaseWriteup(phaseId: string): PhaseWriteup | undefined {
  return PHASE_WRITEUPS[phaseId];
}
