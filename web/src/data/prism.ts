import prismSummary from './prismSummary.json';
import { homeSectionHref } from '../routing/appRoute';

export const GITHUB_REPO = 'https://github.com/amne51ac/project-midas';
export const PRISM_DOCS = `${GITHUB_REPO}/blob/main/research/docs/PRISM_DETECTOR.md`;
export const PRISM_MODULE = `${GITHUB_REPO}/blob/main/research/midas/prism.py`;

export interface MethodComparisonRow {
  id: string;
  name: string;
  era: string;
  planes: string;
  training: string;
  data: string;
  role: string;
}

export interface SoftwareOption {
  id: string;
  title: string;
  verdict: 'recommended' | 'future' | 'not-recommended';
  summary: string;
  pros: string[];
  cons: string[];
}

export interface PrismSection {
  id: string;
  title: string;
  paragraphs: string[];
  bullets?: string[];
}

export interface PrismPageData {
  acronym: string;
  name: string;
  tagline: string;
  lede: string;
  benchmark: typeof prismSummary.benchmark;
  coverage: typeof prismSummary.coverage;
  fit: typeof prismSummary.fit;
  approach: PrismSection[];
  comparisons: MethodComparisonRow[];
  valueAdds: { title: string; body: string }[];
  software: SoftwareOption[];
  limitations: string[];
  roadmap: string[];
}

const b = prismSummary.benchmark;

export const PRISM: PrismPageData = {
  acronym: 'Prism',
  name: 'Photometric Residuals in Sequence Membership',
  tagline: 'A Gaia-era binary anomaly detector for open clusters',
  lede:
    'Prism replaces the legacy Midas Q-value with dual-plane sequence residuals: Gaia BP−RP vs G ' +
    'and W2−BP vs BP−RP. It fuses optical CMD offset with IR pseudocolor on the same stars — ' +
    'the combination Phase III showed Q alone could not recover.',
  benchmark: b,
  coverage: prismSummary.coverage,
  fit: prismSummary.fit,
  approach: [
    {
      id: 'problem',
      title: 'Why not Q?',
      paragraphs: [
        'The Midas Q-value measures how far a star sits below a fixed Yonsei–Yale isochrone in legacy B−V / Mv. On Cantat-Gaudin members it is precise against Malofeeva IR flags but incomplete — most IR-flagged binaries never receive a high Q.',
        'Prism keeps the same goal (flag unresolved pairs on the main sequence) but uses modern photometry and an empirical sequence fit instead of a 2008 isochrone polynomial.',
      ],
    },
    {
      id: 'planes',
      title: 'Two planes, one score',
      paragraphs: [
        'Each star is scored in two independent CMD projections. Positive residuals only — scatter below the single-star locus does not inflate the score.',
      ],
      bullets: [
        'Optical: BP−RP vs G (Gaia DR3) — chromatic / unresolved-blend offset',
        'IR: W2−BP vs BP−RP (Gaia + AllWISE) — IR excess / circumbinary dust',
        'Fusion: score = hypot(max(z_opt, 0), max(z_ir, 0)); optical-only when WISE is missing',
      ],
    },
    {
      id: 'training',
      title: 'Sequence fitting',
      paragraphs: [
        `Training pool: Cantat-Gaudin members with P ≥ ${prismSummary.meta.cgTrainProba}. Low-order polynomials are fit in each plane with iterative σ-clipping (3σ, 3 passes) so known binaries down-weight themselves without needing a pre-cleaned "singles" list — only ~14 uncontaminated singles exist in M34 once Malofeeva is excluded.`,
        'Malofeeva is never used to train Prism. It is reserved for validation, matching the Phase III protocol for Q.',
      ],
    },
  ],
  comparisons: [
    {
      id: 'q',
      name: 'Midas Q-value',
      era: '2008',
      planes: '1 — Mv isochrone offset',
      training: 'Fixed YY isochrone (0.2 Gyr)',
      data: 'Midas BVR',
      role: 'Legacy baseline; high precision, low recall',
    },
    {
      id: 'malofeeva',
      name: 'Malofeeva et al. (2023)',
      era: '2023',
      planes: '1 — W2−BP pseudocolor',
      training: 'Published IR cuts',
      data: 'Gaia + AllWISE',
      role: 'External truth proxy; dominates union fractions',
    },
    {
      id: 'ruwe',
      name: 'Gaia RUWE',
      era: 'Gaia DR3',
      planes: '1 — astrometric quality',
      training: 'Catalog threshold (RUWE > 1.4)',
      data: 'Gaia astrometry',
      role: 'Wide/hierarchical systems; partial overlap',
    },
    {
      id: 'excel',
      name: 'Excel Control',
      era: '2008',
      planes: '1 — B−V spatial filter',
      training: '6th-degree poly + field cut',
      data: 'Midas BVR',
      role: 'Published Midas counts; not Gaia-native',
    },
    {
      id: 'prism',
      name: 'Prism (proposed)',
      era: '2026',
      planes: '2 — Gaia CMD + IR pseudocolor',
      training: 'Empirical sequence + robust clip',
      data: 'Gaia DR3 + AllWISE',
      role: 'Unified anomaly score; replaces Q cut',
    },
  ],
  valueAdds: [
    {
      title: 'Higher recall at similar precision',
      body: `On ${b.n} CG members vs Malofeeva: F1 ${b.prism.f1.toFixed(2)} (Prism, tuned threshold) vs ${b.qValue.f1.toFixed(2)} (legacy Q). Recall rises from ${(b.qValue.recall * 100).toFixed(0)}% to ${(b.prism.recall * 100).toFixed(0)}% while precision stays ${(b.prism.precision * 100).toFixed(0)}%.`,
    },
    {
      title: 'Gaia-native, no legacy isochrone',
      body: 'Optical plane uses the same bands as modern surveys. No Yonsei–Yale age assumption for the primary score — cluster membership comes from Cantat-Gaudin, not Jones–Prosser.',
    },
    {
      title: 'Complementary channels, not a catalog union',
      body: 'Phase IV showed Q-only (4) vs Malofeeva-only (195) stars are largely disjoint. Prism explicitly models both physics channels and fuses them — it is not "flag if any catalog fires."',
    },
    {
      title: 'Portable, reproducible API',
      body: 'Implemented in research/midas/prism.py with a single run_prism() entry point, JSON export, and validation CLI. Designed to extract into a standalone package.',
    },
  ],
  software: [
    {
      id: 'standalone',
      title: 'Standalone Python package (recommended)',
      verdict: 'recommended',
      summary:
        'Extract midas/prism.py into a focused PyPI package (e.g. cluster-prism) with numpy-only core and optional astropy for cone queries.',
      pros: [
        'Fast iteration — no Astropy RFC or multi-year core review cycle',
        'Domain scope is clear: open-cluster binary anomaly scoring, not general astrometry',
        'Dependencies stay minimal; Midas-specific paths remain in project-midas',
        'Versioning and citation (CITATION.cff) under your control',
      ],
      cons: [
        'You maintain releases, docs, and CI',
        'Smaller initial audience than "import astropy.something"',
      ],
    },
    {
      id: 'affiliated',
      title: 'Astropy affiliated package (future path)',
      verdict: 'future',
      summary:
        'If Prism gains cross-cluster validation and community adoption, pursue Astropy Affiliated status — not inclusion in astropy core.',
      pros: [
        'Discoverability via Astropy ecosystem',
        'Shared CI / packaging conventions',
        'Signals stability to reviewers and collaborators',
      ],
      cons: [
        'Requires documented API stability, tests, and maintainer commitment first',
        'Still a separate install — core Astropy will not ship cluster-specific heuristics',
      ],
    },
    {
      id: 'core',
      title: 'Astropy core contribution',
      verdict: 'not-recommended',
      summary:
        'Binary-detection heuristics tied to Gaia+WISE join logic do not belong in astropy core.',
      pros: ['Maximum visibility if accepted (unlikely for this scope)'],
      cons: [
        'Astropy core is for fundamental astronomy primitives, not survey-specific ML/heuristics',
        'Review burden is high; API must serve all of astronomy forever',
        'Prism needs cluster tables, membership probabilities, and IR merges — outside core scope',
      ],
    },
  ],
  limitations: [
    'First benchmark uses Malofeeva as truth — the IR plane partially validates against similar physics. Cross-cluster tests (Pleiades, Hyades) with RV/eclipse truth are required.',
    'Threshold tuning (best F1 ≈ 0.5 on M34) is exploratory; production use needs calibrated P(binary) or fixed cross-cluster thresholds.',
    'Requires Gaia BP/RP and AllWISE W2 — same coverage limits as Malofeeva-style work (~85% dual-plane on CG members).',
    'Still a photometric heuristic, not a dynamical binary model — equal-mass pairs without IR excess remain hard.',
  ],
  roadmap: [
    'Cross-cluster validation notebook (Pleiades / Hyades)',
    'Extract cluster-prism package with pyproject.toml and pytest suite',
    'Web Compare panel overlaying Prism scores on W2−BP diagram',
    'WOCS PRV as sparse spectroscopic anchor',
    'Calibrated posterior P(binary) replacing hard threshold',
  ],
};

export const PRISM_LINKS = {
  findings: '/findings',
  compare: homeSectionHref('compare'),
  tools: homeSectionHref('tools'),
  phase3: '/phases/phase-iii/writeup',
  validateScript: `${GITHUB_REPO}/blob/main/research/scripts/validate_prism.py`,
};
