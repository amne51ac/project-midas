export type ToolStatus = 'ready' | 'partial' | 'adapt' | 'build' | 'replace';

export interface RepoPath {
  label: string;
  path: string;
}

export interface ToolEntry {
  id: string;
  name: string;
  status: ToolStatus;
  exists: string;
  fit: string;
  gap: string;
  action: string;
  phase: string;
  /** Links into this monorepo on GitHub */
  repoPaths?: RepoPath[];
}

export interface ToolCategory {
  id: string;
  title: string;
  summary: string;
  tools: ToolEntry[];
}

export const REPO_URL = 'https://github.com/amne51ac/project-midas';

export function repoBlobUrl(path: string): string {
  return `${REPO_URL}/blob/main/${path}`;
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
      'The original Project Midas deliverables — photometry, membership, isochrones, and Python 2 logic. Preserved with documented provenance and ported to Python 3.',
    tools: [
      {
        id: 'midas-photometry',
        name: 'Midas BVR(I) photometry (~5,749 stars)',
        status: 'ready',
        exists:
          '3,760 pipeline stars after B-band filter; 800-star HR sample and full join table on site (3,738 Gaia-matched).',
        fit: 'Core dataset. Deep multicolor photometry remains valuable for faint stars and for comparing historical reductions to Gaia BP/RP.',
        gap: 'Raw CSV not committed (large); telescope/reduction notes live in Excel README fragments.',
        action: 'Keep raw/ in local or LFS storage; regenerate web JSON after join-table updates.',
        phase: 'Phase I',
        repoPaths: [
          { label: 'Data dictionary', path: 'research/DATA_DICTIONARY.md' },
          { label: 'Web sample builder', path: 'research/scripts/build_web_sample.py' },
          { label: 'Site sample JSON', path: 'web/src/data/m34_sample.json' },
        ],
      },
      {
        id: 'midas-excel',
        name: 'Excel Control workbook & formulas',
        status: 'partial',
        exists:
          'Python 3 reproduces 187 singles / 171 binaries via midas/excel.py; original workbook lives outside this repo.',
        fit: 'Excellent for intuition and regression testing, but not reproducible or scriptable at scale.',
        gap: 'Manual workflow; Excel file not version-controlled here.',
        action: 'Treat Excel as reference; use reproduce_excel_counts.py for regression checks.',
        phase: 'Phase I',
        repoPaths: [
          { label: 'Excel parity module', path: 'research/midas/excel.py' },
          { label: 'Regression script', path: 'research/scripts/reproduce_excel_counts.py' },
        ],
      },
      {
        id: 'midas-py',
        name: 'Midas.py (Python 2 → 3 pipeline)',
        status: 'ready',
        exists: 'research/midas/ package: Mv, Q-value, J&P mating, Excel path, reddening hooks.',
        fit: 'Logic preserved — Excel path (187/171) and legacy ISO/Q path both available.',
        gap: 'Legacy 11th-degree ISO fits differ from Excel 6th-degree poly; use midas/excel.py for Excel parity.',
        action: 'Run run_midas_pipeline.py before cross-match or validation refreshes.',
        phase: 'Phase I',
        repoPaths: [
          { label: 'Pipeline package', path: 'research/midas/' },
          { label: 'CLI runner', path: 'research/scripts/run_midas_pipeline.py' },
          { label: 'Core pipeline', path: 'research/midas/pipeline.py' },
        ],
      },
      {
        id: 'yy-iso',
        name: 'Yonsei–Yale isochrones (ISO.csv)',
        status: 'ready',
        exists: 'Ages 0.08–1.0 Gyr extracted for HR gallery; default analysis age 0.2 Gyr (200 Myr).',
        fit: 'Matches what Midas used; good for reproducing original results and teaching.',
        gap: 'Single metallicity grid; no rotation; superseded for publication-quality age fits.',
        action: 'Keep for reproduction; PARSEC overlay already on site for comparison.',
        phase: 'Phase I–II',
        repoPaths: [
          { label: 'Isochrone builder', path: 'research/scripts/build_isochrones.py' },
          { label: 'Web isochrones', path: 'web/src/data/isochrones.ts' },
          { label: 'Isochrone module', path: 'research/midas/isochrone.py' },
        ],
      },
      {
        id: 'jones-prosser',
        name: 'Jones & Prosser (1996) membership',
        status: 'replace',
        exists: '630 stars ingested via midas/membership.py; 625/630 matched in legacy Python run.',
        fit: 'Historically correct for Midas; inadequate alone for 2020s science (no parallax, limited depth).',
        gap: 'Proper-motion selected only; superseded by Cantat-Gaudin probabilities on join table.',
        action: 'Keep for comparison plots; use cg_member (P≥0.7) as primary membership filter.',
        phase: 'Phase II',
        repoPaths: [{ label: 'Membership loader', path: 'research/midas/membership.py' }],
      },
    ],
  },
  {
    id: 'catalogs',
    title: 'External catalogs & surveys',
    summary:
      'Modern M34 work is a cross-match problem. Catalogs are ingested, joined on m34_join.csv, and exposed in the six-layer data explorer.',
    tools: [
      {
        id: 'gaia-dr3',
        name: 'Gaia DR3',
        status: 'ready',
        exists: '15,211-source field cone (gaia_m34.csv); 3,738 / 3,760 Midas stars matched in m34_join.csv.',
        fit: 'Parallax membership, RUWE astrometric binaries, and source IDs for all downstream work.',
        gap: 'Processed CSVs not committed; DR4 refresh optional later.',
        action: 'Re-run gaia_cone.py + cross_match.py when refreshing field export.',
        phase: 'Phase II',
        repoPaths: [
          { label: 'Gaia cone fetch', path: 'research/scripts/gaia_cone.py' },
          { label: 'Cross-match', path: 'research/scripts/cross_match.py' },
        ],
      },
      {
        id: 'cantat-gaudin',
        name: 'Cantat-Gaudin & Anders (2020) membership',
        status: 'ready',
        exists: '555 UPMASK members ingested; 263 Midas overlaps with cg_member=1 (P≥0.7) on join table.',
        fit: 'Primary probabilistic membership filter for validation and synthesis.',
        gap: 'DR2-based table; optional DR3 membership refresh.',
        action: 'Use cg_proba / cg_member columns in HR filters and Phase IV universe cuts.',
        phase: 'Phase II',
        repoPaths: [
          { label: 'Catalog fetch', path: 'research/scripts/fetch_published_catalogs.py' },
          { label: 'Web catalogs JSON', path: 'research/scripts/build_web_catalogs.py' },
        ],
      },
      {
        id: 'malofeeva',
        name: 'Malofeeva et al. (2023) IR binaries',
        status: 'ready',
        exists: '553 stars on site; 248 Midas overlaps; validation + synthesis truth channel.',
        fit: 'Primary external check on Q-value completeness; sensitive to low mass-ratio pairs B−V misses.',
        gap: 'High overlap with union fraction; diagram on Compare chapter covers W2−BP vs bv0.',
        action: 'Optional H−W1 panel or explorer IR filter for publication figures.',
        phase: 'Phase III–IV',
        repoPaths: [
          { label: 'Validation module', path: 'research/midas/validation.py' },
          { label: 'Phase III runner', path: 'research/scripts/validate_phase3.py' },
        ],
      },
      {
        id: 'wocs',
        name: 'WOCS / Meibom et al. spectroscopic & photometric data',
        status: 'ready',
        exists: '120 VizieR targets ingested; 118 Midas matches; PRV≥90% RV binary truth in validation.',
        fit: 'Gold-standard SB1/SB2 confirmation and rotation periods — ideal validation truth set.',
        gap: 'Only 23 targets carry PRV in VizieR table; full 5,656-star LC archive not ingested.',
        action: 'Treat sparse PRV subset as high-confidence spot checks, not population census.',
        phase: 'Phase III',
        repoPaths: [
          { label: 'WOCS loader', path: 'research/midas/wocs.py' },
          { label: 'Ingest verify', path: 'research/scripts/verify_wocs_ingest.py' },
        ],
      },
      {
        id: 'ir-surveys',
        name: '2MASS + AllWISE photometry',
        status: 'ready',
        exists:
          'Field cache: 3,383 (2MASS) + 6,985 (AllWISE) sources; merged into m34_join_ir.csv — 2,061 / 2,109 Midas matches, 2,089 W2−BP.',
        fit: 'Independent IR color diagrams (Malofeeva-style pseudocolors) on full Midas sample.',
        gap: 'IR columns not yet in web catalog explorer JSON.',
        action: 'Optional: expose W2−BP filter on data explorer after method-compare plots.',
        phase: 'Phase III–IV',
        repoPaths: [
          { label: 'IR fetch', path: 'research/scripts/fetch_ir_photometry.py' },
          { label: 'IR merge', path: 'research/scripts/merge_ir_photometry.py' },
        ],
      },
      {
        id: 'webda',
        name: 'WEBDA / literature photometry compendia',
        status: 'partial',
        exists: 'Online compiled photometry for NGC 1039; referenced in Midas provenance docs.',
        fit: 'Useful for cross-identification and historical context, not primary analysis.',
        gap: 'Scraped HTML tables — awkward for automation; not ingested.',
        action: 'Use selectively for spot checks; prefer Gaia + Midas as canonical photometry.',
        phase: 'Phase I',
        repoPaths: [{ label: 'Research README', path: 'research/README.md' }],
      },
    ],
  },
  {
    id: 'models',
    title: 'Stellar models & isochrones',
    summary:
      'Isochrones turn colors and magnitudes into age and mass estimates. Yonsei–Yale drives the legacy Q-value; PARSEC is overlaid on the site for modern comparison.',
    tools: [
      {
        id: 'parsec-cmd',
        name: 'PARSEC / CMD 3.0 isochrones',
        status: 'ready',
        exists: 'Fetched isochrones built into web/src/data/parsecIsochrones.ts; dashed overlay on HR gallery.',
        fit: 'Updated low-mass physics; standard for open-cluster papers in the 2020s.',
        gap: 'Not wired into Q-value pipeline — comparison layer only.',
        action: 'Use for HR teaching plots; YY remains default for Q and mass bins.',
        phase: 'Phase II',
        repoPaths: [
          { label: 'Fetch script', path: 'research/scripts/fetch_parsec_isochrones.py' },
          { label: 'Web builder', path: 'research/scripts/build_parsec_isochrones.py' },
          { label: 'Site overlay data', path: 'web/src/data/parsecIsochrones.ts' },
        ],
      },
      {
        id: 'mist',
        name: 'MIST isochrones (MESA)',
        status: 'adapt',
        exists: 'Public MIST web tools and grids (external).',
        fit: 'Strong alternative grid; includes rotation physics if needed later.',
        gap: 'No local integration; team has not selected MIST vs PARSEC as secondary grid.',
        action: 'Optional sensitivity check — pick one modern grid for publication plots.',
        phase: 'Phase II',
      },
      {
        id: 'madys',
        name: 'MADYS (Python isochrone fitting package)',
        status: 'partial',
        exists: 'pip-installable package with 17 model grids (2022 A&A); not evaluated here.',
        fit: 'Could replace hand-rolled polynomial fits with principled χ² fitting and uncertainties.',
        gap: 'Not evaluated against legacy Midas counts; learning curve for team.',
        action: 'Prototype one MADYS fit on Gaia-cleaned sample if publishing formal age fits.',
        phase: 'Phase II–III',
      },
      {
        id: 'q-value-heuristic',
        name: 'Midas Q-value binary heuristic',
        status: 'partial',
        exists:
          'Implemented in midas/pipeline.py; Pyodide demo on Code chapter; ROC + synthesis channel in Phase III–IV.',
        fit: 'Fast photometric screen for equal-mass unresolved pairs; best as one channel among several.',
        gap: 'Recall vs Malofeeva only 0.19 at default cut; needs joint tuning with bvdev_single_max.',
        action: 'Calibrate thresholds in q_threshold_calibration.ipynb; report channel-exclusive fractions.',
        phase: 'Phase III–IV',
        repoPaths: [
          { label: 'Pipeline Q logic', path: 'research/midas/pipeline.py' },
          { label: 'Calibration notebook', path: 'research/notebooks/q_threshold_calibration.ipynb' },
          { label: 'Pyodide demos', path: 'web/src/data/codedemos.ts' },
        ],
      },
    ],
  },
  {
    id: 'pipeline',
    title: 'Analysis pipeline',
    summary:
      'Checked-in Python automation from photometry through cross-match, validation, and Phase IV synthesis. Processed CSVs are generated locally (gitignored).',
    tools: [
      {
        id: 'cross-match',
        name: 'Unified cross-match engine',
        status: 'ready',
        exists: 'cross_match.py — Astropy sky matching; m34_join.csv with Gaia, CG, Malofeeva, WOCS, Excel flags, dereddening.',
        fit: 'Central join for every Phase II–IV question.',
        gap: 'Large processed outputs not in git; must re-run after catalog refresh.',
        action: 'Run cross_match.py after pipeline or catalog updates; rebuild web JSON.',
        phase: 'Phase II',
        repoPaths: [
          { label: 'Cross-match script', path: 'research/scripts/cross_match.py' },
          { label: 'Join loader', path: 'research/midas/join_table.py' },
        ],
      },
      {
        id: 'reddening',
        name: 'Reddening & extinction pipeline',
        status: 'ready',
        exists: 'Uniform E(B−V)=0.07 → bv0, mv0 on join table via midas/reddening.py.',
        fit: 'Applied consistently in pipeline, validation, and synthesis.',
        gap: 'No per-star 3D dust map (e.g. Bayestar) — uniform extinction only.',
        action: 'Optional: upgrade to spatially varying E(B−V) for publication HR fits.',
        phase: 'Phase II',
        repoPaths: [{ label: 'Reddening module', path: 'research/midas/reddening.py' }],
      },
      {
        id: 'membership-layer',
        name: 'Probabilistic membership assignment',
        status: 'ready',
        exists: 'cg_proba + cg_member on m34_join.csv; HR diagram and data explorer filters wired.',
        fit: '263 high-confidence members drive validation and synthesis universe.',
        gap: 'Jones–Prosser retained for legacy comparison only.',
        action: 'Keep cg_member threshold documented in DATA_DICTIONARY.md.',
        phase: 'Phase II',
        repoPaths: [{ label: 'Membership module', path: 'research/midas/membership.py' }],
      },
      {
        id: 'validation-stats',
        name: 'Validation & completeness framework',
        status: 'ready',
        exists: 'validation.py + validate_phase3.py — ROC, confusion matrices, bootstrap recall by Mv.',
        fit: 'Phase III complete; Malofeeva / WOCS / RUWE truth sets on CG members.',
        gap: 'WOCS PRV sparse (23 targets); Q recall vs Malofeeva still low (0.19).',
        action: 'Feed channel stats into synthesis and method-compare write-up.',
        phase: 'Phase III',
        repoPaths: [
          { label: 'Validation module', path: 'research/midas/validation.py' },
          { label: 'CLI runner', path: 'research/scripts/validate_phase3.py' },
        ],
      },
      {
        id: 'synthesis',
        name: 'Binary fraction synthesis (deduplicated union)',
        status: 'ready',
        exists:
          'synthesis.py + Compare chapter: overlap tables, f(M), W2−BP vs bv0 diagram (223 CG members with IR).',
        fit: 'Answers “how many binaries?” and “where do channels agree?” without double-counting.',
        gap: 'Union dominated by Malofeeva; formal manuscript still optional.',
        action: 'Optional Zenodo deposit; DR4 Gaia refresh for LAWDS.',
        phase: 'Phase IV',
        repoPaths: [
          { label: 'Synthesis module', path: 'research/midas/synthesis.py' },
          { label: 'Mass mapping', path: 'research/midas/mass.py' },
          { label: 'Web export', path: 'research/scripts/build_web_synthesis.py' },
          { label: 'Diagram export', path: 'web/src/data/methodCompareDiagram.json' },
          { label: 'Compare diagram', path: 'web/src/components/MethodCompareDiagram.tsx' },
        ],
      },
      {
        id: 'wd-pipeline',
        name: 'White dwarf candidate cross-check',
        status: 'ready',
        exists:
          'Rubin et al. (2008) 44 LAWDS candidates; validate_wd_check.py cross-matches Gaia DR3; Compare chapter table.',
        fit: 'Links legacy WD IFMR work to modern astrometry; documents Gaia limits at V ~ 20.',
        gap: 'DR4 not yet wired; half of candidates lack Gaia matches at 2″.',
        action: 'Refresh when Gaia DR4 field export available; optional LAWDS PM from Rubin follow-up.',
        phase: 'Phase IV',
        repoPaths: [
          { label: 'WD module', path: 'research/midas/white_dwarfs.py' },
          { label: 'Rubin ingest', path: 'research/scripts/fetch_rubin_wd.py' },
          { label: 'Web export', path: 'web/src/data/wdCheckSummary.json' },
        ],
      },
    ],
  },
  {
    id: 'infra',
    title: 'Communication, reproducibility & infra',
    summary:
      'The public site, CI deploy, and documentation that make the research reproducible and explorable.',
    tools: [
      {
        id: 'website',
        name: 'Project Midas interactive site',
        status: 'ready',
        exists:
          'Vite + React scrolly site at midasastronomy.com — HR diagram, six-layer catalog explorer, Pyodide demos, phase writeups, path routing, prerendered SEO.',
        fit: 'Methods explainer and catalog browser; static JSON refreshed from pipeline builders.',
        gap: 'No live Gaia TAP proxy; IR columns not yet in explorer JSON.',
        action: 'Rebuild web JSON after pipeline runs; extend explorer for Phase IV IR plots.',
        phase: 'Phase I (ongoing)',
        repoPaths: [
          { label: 'Web app', path: 'web/' },
          { label: 'Home page', path: 'web/src/pages/HomePage.tsx' },
          { label: 'Catalog builder', path: 'research/scripts/build_web_catalogs.py' },
        ],
      },
      {
        id: 'notebooks',
        name: 'Jupyter notebooks',
        status: 'partial',
        exists: 'q_threshold_calibration.ipynb — Q grid, ROC plots vs Malofeeva.',
        fit: 'Exploratory validation and publication figures.',
        gap: 'No membership or synthesis notebooks checked in yet.',
        action: 'Add method-compare and IR color notebooks in Phase IV.',
        phase: 'Phase III–IV',
        repoPaths: [{ label: 'Q calibration', path: 'research/notebooks/q_threshold_calibration.ipynb' }],
      },
      {
        id: 'pyodide-demos',
        name: 'Browser Python demos (Pyodide)',
        status: 'ready',
        exists: 'Eight runnable examples on Code chapter with syntax highlighting.',
        fit: 'Teaches distance modulus, Q-value, PM checks without a local Python install.',
        gap: 'Toy isochrones only — not wired to real m34_sample.json rows.',
        action: 'Optional: add demo loading one real star from the join sample.',
        phase: 'Phase I',
        repoPaths: [
          { label: 'Code runner', path: 'web/src/components/CodeRunner.tsx' },
          { label: 'Demo definitions', path: 'web/src/data/codedemos.ts' },
        ],
      },
      {
        id: 'ci-deploy',
        name: 'GitHub Pages CI',
        status: 'ready',
        exists: '.github/workflows/pages.yml — builds web/ with VITE_BASE_PATH=/ and deploys to midasastronomy.com.',
        fit: 'Static hosting with prerendered route shells and custom domain.',
        gap: 'Python pipeline not in CI yet — manual research/ runs locally.',
        action: 'Optional: add research lint/test job on push.',
        phase: 'Phase I',
        repoPaths: [{ label: 'Pages workflow', path: '.github/workflows/pages.yml' }],
      },
      {
        id: 'reproduction',
        name: 'Reproduction & data release',
        status: 'ready',
        exists:
          'REPRODUCTION.md, run_reproduction.py, build_web_all.py, CITATION.cff; DataRelease on Tools chapter.',
        fit: 'End-to-end rerun from raw Midas CSVs to web JSON; documents gitignored vs checked-in artifacts.',
        gap: 'Processed CSVs not hosted on Zenodo yet; no journal manuscript.',
        action: 'Optional Zenodo DOI for m34_join.csv + synthesis tables.',
        phase: 'Phase IV',
        repoPaths: [
          { label: 'Reproduction guide', path: 'research/REPRODUCTION.md' },
          { label: 'Orchestrator', path: 'research/scripts/run_reproduction.py' },
          { label: 'Web bundle', path: 'research/scripts/build_web_all.py' },
          { label: 'Citation', path: 'CITATION.cff' },
        ],
      },
      {
        id: 'data-dictionary',
        name: 'Data dictionary & provenance doc',
        status: 'ready',
        exists: 'research/DATA_DICTIONARY.md and research/README.md — raw, pipeline, join, and IR columns.',
        fit: 'Column-level schema for every processed table the pipeline emits.',
        gap: 'Telescope/reduction narrative still brief for publication.',
        action: 'Keep in sync when m34_join_ir.csv or synthesis outputs change.',
        phase: 'Phase I',
        repoPaths: [
          { label: 'Data dictionary', path: 'research/DATA_DICTIONARY.md' },
          { label: 'Research README', path: 'research/README.md' },
        ],
      },
    ],
  },
];

export const ECOSYSTEM_TOOLS = [
  { name: 'Astropy + astroquery', role: 'Coordinates, tables, Gaia/VizieR queries', note: 'Standard Python astronomy stack — used in research/scripts/.' },
  { name: 'TOPCAT / STILTS', role: 'Interactive cross-matches', note: 'Fast manual verification before automating joins.' },
  { name: 'Aladin / SkyView', role: 'Visual field inspection', note: 'Sky imagery on the site via fetch_sky_images.sh.' },
  { name: 'numpy / pandas / matplotlib', role: 'Analysis & plots', note: 'Baseline for notebooks and midas/ package.' },
];
