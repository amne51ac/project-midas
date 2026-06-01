export type ToolStatus = 'ready' | 'partial' | 'adapt' | 'build' | 'replace';

export interface ToolEntry {
  id: string;
  name: string;
  status: ToolStatus;
  exists: string;
  fit: string;
  gap: string;
  action: string;
  phase: string;
}

export interface ToolCategory {
  id: string;
  title: string;
  summary: string;
  tools: ToolEntry[];
}

export const STATUS_LABELS: Record<ToolStatus, string> = {
  ready: 'Ready to use',
  partial: 'Partially meets needs',
  adapt: 'Needs adaptation',
  build: 'Must build',
  replace: 'Supersede / retire',
};

export const TOOL_CATEGORIES: ToolCategory[] = [
  {
    id: 'legacy',
    title: 'Legacy Midas assets',
    summary:
      'The original Project Midas deliverables — photometry, membership, isochrones, and Python 2 logic. These are the scientific starting point and must be preserved with documented provenance.',
    tools: [
      {
        id: 'midas-photometry',
        name: 'Midas BVR(I) photometry (~5,749 stars)',
        status: 'ready',
        exists: 'Midas Raw Data.csv in sibling archive; 800-star sample on this site.',
        fit: 'Core dataset. Deep multicolor photometry remains valuable for faint stars and for comparing historical reductions to Gaia BP/RP.',
        gap: 'No unified data dictionary; telescope/date/reduction notes live in Excel README fragments.',
        action: 'Copy into research/data/raw/, document provenance, regenerate web samples via build_web_sample.py.',
        phase: 'Phase I',
      },
      {
        id: 'midas-excel',
        name: 'Excel Control workbook & formulas',
        status: 'partial',
        exists: 'Original Midas Touch.xlsx (parent workspace). Interactive Q-value tuning and accepted singles/binaries counts.',
        fit: 'Excellent for intuition and regression testing, but not reproducible or scriptable at scale.',
        gap: 'Manual workflow; Python 2 era exports; no version-controlled pipeline.',
        action: 'Reproduce key counts in Python 3 and treat Excel as reference, not production path.',
        phase: 'Phase I',
      },
      {
        id: 'midas-py',
        name: 'Midas.py (Python 2 pipeline)',
        status: 'ready',
        exists: 'Ported to research/midas/ (Python 3): Q-value, Excel Control, J&P mating.',
        fit: 'Logic preserved — Excel path (187/171) and legacy ISO/Q path both available.',
        gap: 'Legacy 11th-degree ISO fits differ from Excel 6th-degree poly; use midas/excel.py for Excel parity.',
        action: 'Run run_midas_pipeline.py and reproduce_excel_counts.py in CI.',
        phase: 'Phase I',
      },
      {
        id: 'yy-iso',
        name: 'Yonsei–Yale isochrones (ISO.csv)',
        status: 'ready',
        exists: 'Legacy ISO.csv; ages extracted for website HR diagram and isochrone gallery.',
        fit: 'Matches what Midas used; good for reproducing original results and teaching.',
        gap: 'Single metallicity grid; no rotation; superseded for publication-quality age fits.',
        action: 'Keep for reproduction; add PARSEC/MIST comparison layer in Phase II analysis.',
        phase: 'Phase I–II',
      },
      {
        id: 'jones-prosser',
        name: 'Jones & Prosser (1996) membership',
        status: 'replace',
        exists: 'Members.csv — 630 stars with proper motions and membership codes.',
        fit: 'Historically correct for Midas; inadequate alone for 2020s science (no parallax, limited depth).',
        gap: 'Proper-motion selected only; 406/630 flagged non-member; no probabilistic scores.',
        action: 'Keep for comparison plots; replace primary membership filter with Cantat-Gaudin / Gaia UPMASK.',
        phase: 'Phase II',
      },
    ],
  },
  {
    id: 'catalogs',
    title: 'External catalogs & surveys',
    summary:
      'Modern M34 work is a cross-match problem. These catalogs overlap the same field but answer different questions — astrometry, membership, binaries, rotation.',
    tools: [
      {
        id: 'gaia-dr3',
        name: 'Gaia DR3',
        status: 'partial',
        exists: 'ESA TAP queries; gaia_cone.py template; ~2,500-source field export in research/data/processed/.',
        fit: 'Essential for parallax membership, astrometric binaries (RUWE), and source IDs.',
        gap: 'Not yet joined to every Midas star ID; no automated 5,749-star cross-match table checked into repo.',
        action: 'Build cross-match script (position + PM + parallax); store gaia_source_id on each Midas row.',
        phase: 'Phase II',
      },
      {
        id: 'cantat-gaudin',
        name: 'Cantat-Gaudin & Anders (2020) membership',
        status: 'ready',
        exists: 'VizieR J/A+A/640/A1 (NGC_1039): 555 UPMASK members ingested for the data explorer.',
        fit: 'Best available probabilistic membership for open clusters in the Gaia era.',
        gap: 'DR2-based; needs spatial join to Midas photometry and optional DR3 refresh.',
        action: 'Cross-match CG Gaia IDs to Midas star rows; propagate P(member) into analysis pipeline.',
        phase: 'Phase II',
      },
      {
        id: 'malofeeva',
        name: 'Malofeeva et al. (2023) IR binaries',
        status: 'ready',
        exists: 'VizieR J/AJ/165/45 (NGC 1039): 553 stars with IR two-index pseudocolors on site.',
        fit: 'Primary external check on Q-value completeness; sensitive to low mass-ratio pairs B−V misses.',
        gap: 'Binary flags not in VizieR table; needs cross-match to Midas and Q-value confusion matrix.',
        action: 'Join to Midas/Gaia; classify binary candidates from TID diagram offsets.',
        phase: 'Phase III',
      },
      {
        id: 'wocs',
        name: 'WOCS / Meibom et al. spectroscopic & photometric data',
        status: 'partial',
        exists: 'VizieR J/ApJ/733/115: 120 rotation+RV targets mapped; parent survey = 5,656 V-band LCs.',
        fit: 'Gold-standard SB1/SB2 confirmation and rotation periods — ideal truth set for validation.',
        gap: 'Full 5,656-star light-curve archive not on VizieR; no Midas ID cross-match yet.',
        action: 'Cross-match WOCS/Gaia to Midas IDs; ingest RV binary list for validation stats.',
        phase: 'Phase III',
      },
      {
        id: 'ir-surveys',
        name: '2MASS + AllWISE photometry',
        status: 'ready',
        exists: 'fetch_ir_photometry.py — twomass_m34.csv (3,383) + allwise_m34.csv (6,985) in 0.35° cone.',
        fit: 'Field IR cache for W1−W2 / J−K diagrams independent of published Malofeeva table.',
        gap: 'Not yet merged into m34_join.csv or web explorer.',
        action: 'Cross-match to Gaia BP for Malofeeva-style W2−BP cuts on all members.',
        phase: 'Phase III',
      },
      {
        id: 'webda',
        name: 'WEBDA / literature photometry compendia',
        status: 'partial',
        exists: 'Online compiled photometry for NGC 1039; referenced in Midas provenance.',
        fit: 'Useful for cross-identification and historical context, not primary analysis.',
        gap: 'Scraped HTML tables — awkward for automation.',
        action: 'Use selectively for spot checks; prefer Gaia + Midas as canonical photometry.',
        phase: 'Phase I',
      },
    ],
  },
  {
    id: 'models',
    title: 'Stellar models & isochrones',
    summary:
      'Isochrones turn colors and magnitudes into age and mass estimates. Midas used Yonsei–Yale; modern work should compare multiple grids.',
    tools: [
      {
        id: 'parsec-cmd',
        name: 'PARSEC / CMD 3.0 isochrones',
        status: 'adapt',
        exists: 'Public web interface and downloadable isochrones (Padova group).',
        fit: 'Updated low-mass physics; standard for open-cluster papers in the 2020s.',
        gap: 'Not wired into Midas Q-value pipeline; E(B−V) = 0.07 needs consistent application.',
        action: 'Download solar-metallicity isochrones at 180–220 Myr; overlay on HR diagram; compare turnoff to YY.',
        phase: 'Phase II',
      },
      {
        id: 'mist',
        name: 'MIST isochrones (MESA)',
        status: 'adapt',
        exists: 'Public MIST web tools and grids.',
        fit: 'Strong alternative grid; includes rotation physics if needed later.',
        gap: 'No local integration; team has not selected MIST vs PARSEC as primary.',
        action: 'Optional sensitivity check in Phase II — pick one modern grid for publication plots.',
        phase: 'Phase II',
      },
      {
        id: 'madys',
        name: 'MADYS (Python isochrone fitting package)',
        status: 'partial',
        exists: 'pip-installable package with 17 model grids (2022 A&A).',
        fit: 'Could replace hand-rolled polynomial fits with principled χ² fitting and uncertainties.',
        gap: 'Not evaluated against legacy Midas counts; learning curve for team.',
        action: 'Prototype one MADYS fit on Gaia-cleaned sample; compare age/binary flags to legacy Q-value.',
        phase: 'Phase II–III',
      },
      {
        id: 'q-value-heuristic',
        name: 'Midas Q-value binary heuristic',
        status: 'adapt',
        exists: 'Implemented in Midas.py; explained on this site with runnable Pyodide demo.',
        fit: 'Fast photometric screen for equal-mass unresolved pairs; scientifically dated as sole discriminator.',
        gap: 'No completeness/contamination estimates; fixed ΔM_V; no IR or RV confirmation layer.',
        action: 'Calibrate Q thresholds against Malofeeva + WOCS; report ROC curves, not just candidate lists.',
        phase: 'Phase III',
      },
    ],
  },
  {
    id: 'pipeline',
    title: 'Analysis pipeline (to build)',
    summary:
      'These are the glue scripts and workflows that turn catalogs + models into reproducible science products. Most do not exist yet as checked-in automation.',
    tools: [
      {
        id: 'cross-match',
        name: 'Unified cross-match engine',
        status: 'build',
        exists: 'Manual cone queries and prototype gaia_m34.csv only.',
        fit: 'Required for every Phase II–IV question.',
        gap: 'No script matching Midas IDs ↔ Gaia ↔ Cantat-Gaudin ↔ Malofeeva with configurable radii and PM cuts.',
        action: 'Build research/scripts/cross_match.py with Astropy.coordinates + output join table (Parquet/CSV).',
        phase: 'Phase II',
      },
      {
        id: 'reddening',
        name: 'Reddening & extinction pipeline',
        status: 'build',
        exists: 'Literature E(B−V) ≈ 0.07 for M34; not applied in web sample or scripts.',
        fit: 'Essential before comparing observed B−V to isochrones at optical wavelengths.',
        gap: 'No dereddening module; no 3D dust map integration (e.g. Bayestar).',
        action: 'Apply uniform E(B−V)=0.07 first; optionally upgrade to per-star Bayestar later.',
        phase: 'Phase II',
      },
      {
        id: 'membership-layer',
        name: 'Probabilistic membership assignment',
        status: 'build',
        exists: 'Gaia parallax cut used as proxy in web catalog explorer only.',
        fit: 'Field contamination is the main limiter on binary fraction measurements.',
        gap: 'No P(member) column on Midas stars; Jones–Prosser still the only local membership file.',
        action: 'Merge Cantat-Gaudin probabilities; flag field stars; export membership column for HR diagrams.',
        phase: 'Phase II',
      },
      {
        id: 'validation-stats',
        name: 'Validation & completeness framework',
        status: 'build',
        exists: 'Research questions listed; no ROC/confusion matrix code.',
        fit: 'Required to publish method comparison credibly.',
        gap: 'No bootstrap, no truth-set joins, no binary fraction vs. mass bins.',
        action: 'Notebook: Q-value vs Malofeeva vs WOCS RV; report completeness and contamination by magnitude.',
        phase: 'Phase III',
      },
      {
        id: 'wd-pipeline',
        name: 'White dwarf candidate cross-check',
        status: 'build',
        exists: 'Rubin et al. candidates cited in roadmap questions only.',
        fit: 'Niche but timely for IFMR / WD binary literature.',
        gap: 'No WD sample ingested; no Gaia DR4 astrometry check.',
        action: 'Low priority until Phase IV — ingest Rubin list when core binary validation is done.',
        phase: 'Phase IV',
      },
    ],
  },
  {
    id: 'infra',
    title: 'Communication, reproducibility & infra',
    summary:
      'Tools for sharing results with the team and the public. Several already exist from the website build; others are still aspirational.',
    tools: [
      {
        id: 'website',
        name: 'Project Midas interactive site (this repo)',
        status: 'partial',
        exists: 'Vite + React scrolly site with HR diagram, catalog explorer, Pyodide demos, CI deploy.',
        fit: 'Strong outreach and methods explainer; not yet a live analysis dashboard.',
        gap: 'Static JSON samples; no live Gaia cone queries; catalog cross-match incomplete.',
        action: 'Refresh processed JSON after each pipeline run; optional live TAP proxy (future).',
        phase: 'Phase I (ongoing)',
      },
      {
        id: 'notebooks',
        name: 'Jupyter notebooks (research/)',
        status: 'build',
        exists: 'Folder scaffolded; scripts only, no checked-in notebooks yet.',
        fit: 'Standard for exploratory validation and publication figures.',
        gap: 'Empty notebooks/ directory.',
        action: 'Add membership cross-match and validation notebooks as pipeline matures.',
        phase: 'Phase II–III',
      },
      {
        id: 'pyodide-demos',
        name: 'Browser Python demos (Pyodide)',
        status: 'ready',
        exists: 'Eight runnable examples on Code chapter with syntax highlighting.',
        fit: 'Educational — teaches distance modulus, Q-value, PM checks without a local Python install.',
        gap: 'Not connected to real Midas star rows; toy isochrones only.',
        action: 'Optional: add demo that loads one real star from m34_sample.json.',
        phase: 'Phase I',
      },
      {
        id: 'ci-deploy',
        name: 'GitHub / GitLab Pages CI',
        status: 'ready',
        exists: 'Workflow files in .github/ and .gitlab-ci.yml; npm build verified.',
        fit: 'Meets static hosting needs for the public site.',
        gap: 'Placeholder repo URLs in footer; VITE_BASE_PATH must match deploy path.',
        action: 'Set real remote URLs when repository is published.',
        phase: 'Phase I',
      },
      {
        id: 'data-dictionary',
        name: 'Data dictionary & provenance doc',
        status: 'ready',
        exists: 'research/DATA_DICTIONARY.md and README data-source tables.',
        fit: 'Column-level schema for raw CSVs, pipeline output, and join table.',
        gap: 'Telescope/reduction narrative still brief — expand PROVENANCE when publishing.',
        action: 'Keep DATA_DICTIONARY.md in sync when processed/ columns change.',
        phase: 'Phase I',
      },
    ],
  },
];

export const ECOSYSTEM_TOOLS = [
  { name: 'Astropy + astroquery', role: 'Coordinates, tables, Gaia/VizieR queries', note: 'Standard Python astronomy stack — adopt everywhere.' },
  { name: 'TOPCAT / STILTS', role: 'Interactive cross-matches', note: 'Fast manual verification before automating joins.' },
  { name: 'Aladin / SkyView', role: 'Visual field inspection', note: 'Already used for aligned comparison images on this site.' },
  { name: 'numpy / pandas / matplotlib', role: 'Analysis & plots', note: 'Baseline for notebooks and ported Midas.py.' },
];
