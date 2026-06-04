import credenceSummary from './credenceSummary.json';
import { homeSectionHref } from '../routing/appRoute';

export const GITHUB_REPO = 'https://github.com/amne51ac/project-midas';
export const CREDENCE_ARCHITECTURE = `${GITHUB_REPO}/blob/main/research/docs/CREDENCE_ARCHITECTURE.md`;
export const CREDENCE_ML_STRATEGY = `${GITHUB_REPO}/blob/main/research/docs/CREDENCE_ML_DATA_STRATEGY.md`;
export const CREDENCE_DOCS = `${GITHUB_REPO}/blob/main/research/docs/CREDENCE.md`;
export const CREDENCE_MODULE = `${GITHUB_REPO}/blob/main/research/midas/credence/`;

export const CREDENCE_SECTIONS = [
  { id: 'vision', label: 'Vision' },
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'design', label: 'Design' },
  { id: 'data', label: 'Data scope' },
  { id: 'membership', label: 'Membership' },
  { id: 'infer', label: 'Infer' },
  { id: 'display', label: 'Display' },
  { id: 'software', label: 'Software' },
  { id: 'roadmap', label: 'Roadmap' },
] as const;

export interface CredenceSection {
  id: string;
  title: string;
  paragraphs: string[];
  bullets?: string[];
}

export interface DataTier {
  id: string;
  label: string;
  clusters: string;
  stars: string;
  modalities: string;
  purpose: string;
}

export interface PipelineStep {
  id: string;
  title: string;
  summary: string;
  deliverables: string[];
}

export interface SoftwareOption {
  id: string;
  title: string;
  verdict: 'recommended' | 'future' | 'not-recommended';
  summary: string;
  pros: string[];
  cons: string[];
}

export interface DisplayFeature {
  title: string;
  body: string;
}

const b = credenceSummary.benchmark;

export const CREDENCE = {
  name: 'Credence',
  tagline: 'Ingest. Resolve. Infer. Display.',
  lede:
    'Credence is one pipeline for open-cluster stars: ingest published membership and survey data, ' +
    'resolve each star into a unified record, infer a credence vector against a cluster baseline, ' +
    'and display the result in a planetarium-style sky atlas. Project Midas Phases I–IV validated ' +
    'ingest → resolve → infer on M34; Credence adds galaxy-scale scope, unified storage, and the display layer.',

  glance: [
    { label: 'Pipeline', value: '4 steps', detail: 'Ingest · resolve · infer · display' },
    { label: 'Primary population', value: '~3.5k–7k OCs', detail: 'Known Gaia-era catalogs' },
    { label: 'Scale target', value: '~10⁶ stars', detail: 'Member rows at T2 rollout' },
    {
      label: 'M34 infer',
      value: `${b.n} CG members`,
      detail: `F1 ≈ ${b.credence.f1.toFixed(2)} (in-sample; T0 cluster CV next)`,
    },
  ],

  vision: {
    id: 'vision',
    title: 'What Credence is',
    paragraphs: [
      'Phase IV showed that catalog unions (Q, Malofeeva, WOCS, RUWE) overlap weakly — flags are not a model. ' +
        'Credence replaces that with a single resolved star, a cluster-conditioned baseline, and a vector of credences ' +
        'you can filter, cite, and explore on the sky.',
      'Membership discovery (UPMASK, HDBSCAN) stays upstream. Credence consumes P(member) from Cantat-Gaudin and Hunt; ' +
        'it does not rebuild the cluster census.',
    ],
    bullets: [
      'Ingest — Hunt/CG lists, Gaia, WISE, literature tables into one store',
      'Resolve — cross-match to StarEntity with sparse modalities',
      'Infer — multimodal MLP → credence vector (p_binary, channel heads)',
      'Display — Credence Atlas: pan/zoom celestial sphere, layer toggles',
    ],
  } satisfies CredenceSection,

  pipeline: {
    title: 'Ingest → resolve → infer → display',
    paragraphs: [
      'Each step has a clear boundary. M34 today runs ingest/resolve through cross_match.py and merge_ir_photometry.py; ' +
        'infer through midas/credence/ (PyTorch MLP); display is the next build (/atlas).',
    ],
    steps: [
      {
        id: 'ingest',
        title: '1 · Ingest',
        summary: 'Pull membership and survey data into normalized tables — not per-cluster one-offs.',
        deliverables: [
          'Cluster registry + membership rows (P_member from CG/Hunt)',
          'Bulk Gaia / AllWISE by member source_id',
          'DuckDB or Parquet as the spine; Midas BVR where it exists',
        ],
      },
      {
        id: 'resolve',
        title: '2 · Resolve',
        summary: 'One row per physical star: Gaia source_id, positions, sparse modality payloads, cluster attachment.',
        deliverables: [
          'StarEntity schema (generalize m34_join_ir.csv)',
          'Provenance per channel — what was measured, what was missing',
          'M34: cross_match.py + merge_ir_photometry.py (done)',
        ],
      },
      {
        id: 'infer',
        title: '3 · Infer',
        summary:
          'Train a cluster-conditioned MLP on Gaia + WISE + context; output credence vector per star.',
        deliverables: [
          'midas/credence/ — CredenceInferModel (Gaia + WISE encoders, multi-head)',
          'p_binary, p_cmd, p_ir, p_ruwe + membership weight',
          'Cluster-held-out validation as T0 clusters join the store',
        ],
      },
      {
        id: 'display',
        title: '4 · Display',
        summary:
          'Credence Atlas — planetarium view from Earth, pan/zoom, credence-colored stars, cluster hulls.',
        deliverables: [
          '/atlas route — celestial sphere, no free-flight camera',
          'Filters: membership, credence, data source, cluster context',
          'Pop-sky labels (constellations, Messier) as navigation chrome',
        ],
      },
    ] satisfies PipelineStep[],
  },

  design: {
    title: 'Design & architecture',
    lede:
      'Credence is a store-backed pipeline: external catalogs flow in through ingest, resolve produces StarEntity records, ' +
      'infer writes CredenceVectors, display serves tiles to the Atlas. Membership discovery stays upstream.',
    diagram: `External catalogs (CG, Hunt, Gaia, WISE, literature)
        │
        ▼ ingest
   Credence store (DuckDB / Parquet)
   clusters · membership · stars · modalities · credences
        │
        ├── resolve  → StarEntity (sparse modalities)
        ├── infer    → CredenceVector (per star / cluster)
        └── display  → tiles / API → Credence Atlas`,
    starEntity: [
      'identity: gaia_source_id (+ optional legacy id)',
      'astrometry: ra, dec, parallax, proper motions',
      'cluster_links: [{ cluster_id, p_member, catalog }]',
      'modalities: gaia · wise · twomass · legacy_bvr · literature (sparse — null if missing)',
    ],
    credenceVector: [
      'p_member — ingested (credence dimension 0)',
      'p_binary — fused binary posterior (primary infer head)',
      'p_cmd, p_ir, p_ruwe — channel heads (CMD, IR pseudocolor, astrometric)',
      'score_infer — legacy fused residual (optional export)',
      'planes — "dual" | "optical_only"',
      'model_version, computed_at',
    ],
    storage: [
      'L0 clusters (~10³) · L1 membership (~10⁶) · L2 stars · L3 modalities (sparse)',
      'L4 baselines · L5 credences · L6 display tiles',
      'Research: DuckDB + Parquet · Release: Zenodo · Atlas: object storage + API',
    ],
    m34Mapping: [
      'Ingest: fetch_*.py, raw/processed CSVs',
      'Resolve: cross_match.py → m34_join_ir.csv',
      'Infer: midas/credence/ → credence_model.pt + credence_summary.json',
      'Display: DataExplorer today → /atlas (planned)',
    ],
    inferEngine: {
      title: 'Infer engine (credence-mlp-v1)',
      note:
        'PyTorch multimodal MLP: separate Gaia and WISE encoders, cluster context, multi-head outputs. ' +
        'Ingest, resolve, and display are unchanged — only infer is model-based.',
      architecture: [
        'Gaia encoder: G, BP−RP, RUWE (+ missingness masks)',
        'WISE encoder: W2−BP (+ mask when AllWISE absent)',
        'Cluster context: distance, age priors, member density',
        'Heads: p_binary (primary), p_cmd, p_ir, p_ruwe',
      ],
      next: [
        'T0 multi-cluster training with cluster-held-out evaluation',
        'Uncertainty calibration and isotonic p_binary tuning at scale',
        'Optional Gaia XP encoder; spectroscopic fine-tune (T3+)',
      ],
    },
    mlDataStrategy: {
      title: 'ML training & evaluation plan',
      lede:
        'Meaningful infer ML needs diverse clusters and cluster-held-out tests — not M34 alone or a random split on ~10⁶ members.',
      verdicts: [
        {
          approach: 'M34 only (~263 members)',
          verdict: 'Plumbing only',
          note: 'One cluster; Malofeeva is training target and benchmark; F1 ≈ 0.96 is not held-out.',
        },
        {
          approach: 'Full census, random star train/test',
          verdict: 'Not recommended',
          note: 'Leaks cluster structure; labels do not scale with member count.',
        },
        {
          approach: 'T0: 5–10 clusters, cluster-held-out',
          verdict: 'Recommended next',
          note: '~10⁴–10⁵ stars; train on N−1 clusters, test on held-out cluster(s).',
        },
        {
          approach: 'T1/T2 scale after harness',
          verdict: 'Production path',
          note: 'Pretrain on all Gaia+WISE members optional; eval still cluster-CV.',
        },
      ],
      m34Today: [
        'Source: m34_join_ir.csv — 3,760 rows scored; 263 CG members (P ≥ 0.7) in training pool',
        'Train: 224 stars · Val: 39 (random split, same cluster) — val is not the reported benchmark',
        'Benchmark: all 263 members vs Malofeeva — overlaps training set',
        'Labels: Malofeeva (binary + IR heads), Excel CMD, RUWE — weighted by P(member)',
      ],
      protocol: [
        'Split by cluster_id — never leak a test cluster into training gradients',
        'Weak labels (Malofeeva, RUWE) down-weighted; gold (RV, eclipsing) where sparse',
        'Report per-channel and per-cluster metrics — not one global F1',
        'Beat legacy Q on held-out clusters at matched precision',
      ],
    },
  },

  dataScope: {
    title: 'Galaxy-scale tiers (not M34-only)',
    paragraphs: [
      'M34 is the guided tour — rare legacy BVR depth. Galaxy-scale Credence runs on Gaia + WISE + ' +
        'published membership. The ~730M Gaia search pool is for cluster finders, not atlas rendering.',
    ],
    tiers: [
      {
        id: 't0',
        label: 'T0 · Benchmark',
        clusters: '5–10',
        stars: '10⁴–10⁵',
        modalities: 'Gaia + WISE + literature labels',
        purpose: 'Cluster-held-out infer ML; Pleiades, Hyades, M34, Praesepe, …',
      },
      {
        id: 't1',
        label: 'T1 · Bright census',
        clusters: '~1,500–2,000',
        stars: '~2–3 × 10⁵',
        modalities: 'Gaia + WISE (G ≲ 18)',
        purpose: 'Scale training + calibration (cluster CV)',
      },
      {
        id: 't2',
        label: 'T2 · Hunt HQ OCs',
        clusters: '~3,530',
        stars: '~10⁶',
        modalities: 'Gaia + WISE + cluster params',
        purpose: 'Production atlas v1',
      },
      {
        id: 't3',
        label: 'T3 · Full + XP',
        clusters: '~7,167',
        stars: '10⁶–10⁷',
        modalities: '+ Gaia XP, optional light curves',
        purpose: 'Research-scale releases',
      },
    ] satisfies DataTier[],
    storageNote:
      'Clusters (~10³) + membership (~10⁶) + modalities + credence vectors ≈ 1–5 GB without Gaia XP.',
  },

  membership: {
    id: 'membership',
    title: 'Membership: ingest, not discover',
    paragraphs: [
      'Cantat-Gaudin and Hunt publish P(member). Credence ingests those lists for ingest/resolve and uses P(member) ' +
        'as credence dimension zero when inferring and displaying.',
      'On M34: 263 high-confidence CG members (P ≥ 0.7) vs 630 legacy Jones–Prosser rows. Infer trains on CG, not J&P.',
    ],
    bullets: [
      'In scope: ingest membership, weight baseline fit, atlas filters',
      'Out of scope v1: all-sky UPMASK/HDBSCAN rerun',
      'Show catalog source and threshold in the UI — not a false binary member flag',
    ],
  },

  infer: {
    title: 'Infer — M34 benchmark',
    note:
      `${credenceSummary.meta.description} — ${credenceSummary.meta.version} in midas/credence/. ` +
        'M34 prototype only: see ML training plan for why reported F1 is not a held-out test.',
    benchmark: b,
    coverage: credenceSummary.coverage,
    model: credenceSummary.model,
    planes: [
      'Gaia branch: photometry + RUWE with missingness masks',
      'WISE branch: W2−BP pseudocolor when AllWISE is present',
      'Trunk: cluster context + P(member) → p_binary and channel heads',
    ],
    training:
      `CG members P ≥ ${credenceSummary.meta.cgTrainProba}: ` +
        `${credenceSummary.model.nTrain} train / ${credenceSummary.model.nVal} val · ` +
        `${credenceSummary.model.epochs} epochs · hidden ${credenceSummary.model.hiddenDim}`,
  },

  display: {
    title: 'Display — Credence Atlas',
    paragraphs: [
      'The product surface: a planetarium from Earth’s perspective — drag to pan, scroll to zoom field of view. ' +
        'Stars colored and filtered by credence; cluster hulls and familiar sky labels for navigation.',
    ],
    features: [
      {
        title: 'Layer toggles',
        body: 'P(member), p_binary, survey provenance (Gaia, WISE, WOCS, legacy Midas).',
      },
      {
        title: 'Color modes',
        body: 'G magnitude, infer score, RUWE, channel-specific credences with uncertainty.',
      },
      {
        title: 'Cluster context',
        body: 'Fly-to NGC 1039, show member cloud and baseline panel.',
      },
      {
        title: 'Rollout',
        body: 'v0 M34 → named clusters → region-loaded T1 census → share URLs.',
      },
    ] satisfies DisplayFeature[],
    database: {
      title: 'Unified store (feeds display)',
      paragraphs: ['Pipeline writes to DuckDB/Parquet; atlas reads tiles or API — not 15 MB static JSON per page.'],
      tables: [
        'clusters — registry and parameters',
        'stars — Gaia identity + astrometry',
        'membership — star_id, cluster_id, p_member',
        'credences — infer outputs per star/cluster',
        'modalities — sparse survey payloads',
        'overlays — hulls, constellations, named objects',
      ],
    },
  },

  software: [
    {
      id: 'package',
      title: 'cluster-credence Python package',
      verdict: 'recommended',
      summary: 'Ingest + resolve + infer CLI; numpy core, optional Astropy. PyPI: cluster-credence.',
      pros: ['One pipeline, one install', 'Zenodo DOI under our control'],
      cons: ['We maintain releases and cross-cluster validation'],
    },
    {
      id: 'atlas',
      title: 'Credence Atlas (web)',
      verdict: 'recommended',
      summary: '/atlas — planetarium display layer. Midas site keeps Phases I–IV as the paper trail.',
      pros: ['Shows the full ingest→display story', 'Starts from m34_join_ir + credence scores'],
      cons: ['Tile infra before T2 scale'],
    },
    {
      id: 'affiliated',
      title: 'Astropy affiliated package',
      verdict: 'future',
      summary: 'After stable API and cross-cluster benchmarks — not core Astropy.',
      pros: ['Ecosystem discoverability'],
      cons: ['Maintainer commitment first'],
    },
  ] satisfies SoftwareOption[],

  midasLink: {
    title: 'Relationship to Project Midas',
    paragraphs: [
      'Phases I–IV are the M34 archive: legacy ingest, resolve, validation, synthesis. Credence is the generalization ' +
        'and the path to display at scale.',
    ],
  },

  limitations: [
    'M34 F1 uses Malofeeva as training target and benchmark — not cluster-held-out.',
    'Random 224/39 train/val on one cluster does not prove cross-cluster generalization.',
    'Membership catalogs disagree at faint limits; credences must show uncertainty.',
    'Legacy Midas-depth BVR exists for ~10¹ clusters, not galaxy scale.',
  ],

  roadmap: [
    'v0: credence-mlp-v1 on M34 — infer plumbing (done)',
    'v1: Credence Atlas on M34 — display layer',
    'v2: T0 ingest (5–10 clusters) + cluster-held-out credence-mlp-v2',
    'v3: T1 scale (~3×10⁵), calibration + region tiles',
    'v4: T2 production infer (~10⁶) + Zenodo release',
    'v5: Gaia XP encoder; spectroscopic fine-tune on gold labels',
  ],
};

export const CREDENCE_LINKS = {
  findings: '/continued/findings',
  compare: homeSectionHref('compare'),
  data: homeSectionHref('data'),
  tools: '/continued/tools',
  docs: CREDENCE_DOCS,
  architecture: CREDENCE_ARCHITECTURE,
  mlStrategy: CREDENCE_ML_STRATEGY,
  module: CREDENCE_MODULE,
  validateScript: `${GITHUB_REPO}/blob/main/research/scripts/validate_credence.py`,
};
