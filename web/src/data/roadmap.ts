export type WorkStatus = 'done' | 'in_progress' | 'planned';

export type PhaseStatus = 'complete' | 'active' | 'upcoming';

export interface RoadmapTask {
  id: string;
  title: string;
  status: WorkStatus;
  detail?: string;
  /** ISO date (YYYY-MM-DD) when status became complete */
  completedDate?: string;
}

export interface PhaseExploration {
  id: string;
  title: string;
  summary: string;
  /** Hash link on the main scrolly site, e.g. `#code` */
  homeHref?: string;
  /** Highlight stat or metric shown on the card */
  stat?: string;
}

export interface RoadmapPhase {
  id: string;
  label: string;
  title: string;
  summary: string;
  status: PhaseStatus;
  /** ISO date when the phase was marked complete */
  completedDate?: string;
  tasks: RoadmapTask[];
  explorations: PhaseExploration[];
}

export const WORK_STATUS_LABELS: Record<WorkStatus, string> = {
  done: 'Complete',
  in_progress: 'In progress',
  planned: 'Planned',
};

export const PHASE_STATUS_LABELS: Record<PhaseStatus, string> = {
  complete: 'Complete',
  active: 'In progress',
  upcoming: 'Upcoming',
};

export function formatCompletedDate(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export const ROADMAP_PHASES: RoadmapPhase[] = [
  {
    id: 'phase-i',
    label: 'Phase I',
    title: 'Archaeology & reproducibility',
    summary:
      'Document legacy photometry provenance, port pipelines to Python 3, reproduce Excel singles/binaries counts, and publish this site.',
    status: 'complete',
    completedDate: '2026-06-01',
    explorations: [
      {
        id: 'hr-scrolly',
        title: 'HR diagram walkthrough',
        summary: 'Scroll from raw photometry through isochrones to the binary track that defines Midas.',
        homeHref: '#science',
        stat: '7 scrolly steps',
      },
      {
        id: 'pyodide',
        title: 'Try the arithmetic',
        summary: 'Eight browser Python demos — distance modulus, Q-value, proper motion checks.',
        homeHref: '#code',
        stat: '8 demos',
      },
      {
        id: 'excel',
        title: 'Excel Control reproduction',
        summary: 'Python 3 reproduces 187 accepted singles and 171 binaries from the original workbook.',
        homeHref: '#compare',
        stat: '187 / 171',
      },
      {
        id: 'tools',
        title: 'Toolchain inventory',
        summary: 'Legacy archive vs Python 3 port — provenance, DATA_DICTIONARY.md, CI, and open gaps.',
        homeHref: '#tools',
      },
    ],
    tasks: [
      {
        id: 'site',
        title: 'Interactive scrolly site (HR diagram, catalog explorer, mobile layout)',
        status: 'done',
        completedDate: '2026-05-31',
        detail: 'Vite + React site with Chapters 1–7, CI deploy, and dark-sky styling.',
      },
      {
        id: 'pyodide',
        title: 'Browser Python demos (Pyodide arithmetic examples)',
        status: 'done',
        completedDate: '2026-05-31',
        detail: 'Eight runnable examples on the Code chapter with syntax highlighting.',
      },
      {
        id: 'isochrones',
        title: 'Yonsei–Yale isochrones for web HR diagram',
        status: 'done',
        completedDate: '2026-05-31',
        detail: 'build_isochrones.py regenerates clean age tracks from legacy ISO.csv.',
      },
      {
        id: 'ci',
        title: 'GitHub / GitLab Pages CI workflows',
        status: 'done',
        completedDate: '2026-05-31',
        detail: 'Static build verified; set VITE_BASE_PATH when publishing.',
      },
      {
        id: 'provenance',
        title: 'Legacy photometry provenance documentation',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'research/README.md, DATA_DICTIONARY.md, and midas.paths document sources and columns.',
      },
      {
        id: 'py3-port',
        title: 'Port Midas.py pipeline to Python 3',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'research/midas/ package + run_midas_pipeline.py (Mv, Q-value, J&P mating).',
      },
      {
        id: 'excel-regression',
        title: 'Reproduce Excel singles / binaries counts',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'reproduce_excel_counts.py matches Control sheet 187/171 via midas/excel.py.',
      },
      {
        id: 'data-dict',
        title: 'Data dictionary for Midas CSV columns',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'research/DATA_DICTIONARY.md covers raw, pipeline, and join outputs.',
      },
    ],
  },
  {
    id: 'phase-ii',
    label: 'Phase II',
    title: 'Gaia integration',
    summary:
      'Cross-match all Midas stars to Gaia DR3; replace Jones–Prosser membership with Cantat-Gaudin probabilities; apply reddening corrections.',
    status: 'complete',
    completedDate: '2026-06-01',
    explorations: [
      {
        id: 'catalog-map',
        title: 'Multi-catalog sky map',
        summary: 'Gaia DR3 field (15,211 sources) plus Midas, Cantat-Gaudin, Malofeeva, and WOCS layers.',
        homeHref: '#data',
        stat: '6 layers',
      },
      {
        id: 'hr-filters',
        title: 'Membership, reddening & PARSEC',
        summary: 'De-reddened HR view, Cantat-Gaudin member filter, and PARSEC vs YY isochrone overlay.',
        homeHref: '#science',
        stat: 'E(B−V)=0.07',
      },
      {
        id: 'join',
        title: 'Unified join table',
        summary: 'm34_join.csv links 3,760 Midas stars to Gaia and catalog flags — 99.4% Gaia match rate.',
        homeHref: '#compare',
        stat: '3,738 Gaia',
      },
      {
        id: 'cross-match',
        title: 'Cross-match pipeline',
        summary: 'research/scripts/cross_match.py — positional joins with Excel singles/binaries flags.',
        homeHref: '#data',
        stat: '263 CG',
      },
      {
        id: 'compare',
        title: 'Joining the layers',
        summary: 'How we avoid double-counting when merging photometric, IR, and RV binary diagnostics.',
        homeHref: '#compare',
      },
    ],
    tasks: [
      {
        id: 'cantat',
        title: 'Ingest Cantat-Gaudin UPMASK membership (555 stars)',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'VizieR J/A+A/640/A1 on data explorer; 263 overlap Midas photometry in join table.',
      },
      {
        id: 'malofeeva-ingest',
        title: 'Ingest Malofeeva et al. IR binary sample (553 stars)',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'VizieR J/AJ/165/45 on data explorer; 248 overlap in m34_join.csv.',
      },
      {
        id: 'gaia-field',
        title: 'Gaia DR3 field export around M34',
        status: 'done',
        completedDate: '2026-06-01',
        detail: '15,211 sources in gaia_m34.csv via gaia_cone.py (0.5° cone).',
      },
      {
        id: 'cross-match',
        title: 'Unified cross_match.py (Midas ↔ Gaia ↔ catalogs)',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'Astropy sky matching; m34_join.csv with Gaia IDs, CG proba, Malofeeva/WOCS flags.',
      },
      {
        id: 'wocs-ingest',
        title: 'Ingest WOCS / Meibom RV + rotation targets',
        status: 'done',
        completedDate: '2026-06-01',
        detail: '120 VizieR targets (J/ApJ/733/115/table2); 118 matched to Midas photometry. Seq 2 & 89 outside B-band sample.',
      },
      {
        id: 'membership',
        title: 'Probabilistic membership on all Midas stars',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'cg_proba + cg_member (P≥0.7) on m34_join.csv; HR diagram and data explorer filters.',
      },
      {
        id: 'reddening',
        title: 'Reddening / dereddening pipeline (E(B−V) ≈ 0.07)',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'midas/reddening.py — uniform E(B−V)=0.07 → bv0, mv0 in join table; optional --ebv on pipeline.',
      },
      {
        id: 'parsec',
        title: 'PARSEC isochrone comparison layer',
        status: 'done',
        completedDate: '2026-06-01',
        detail: 'fetch_parsec_isochrones.py + build_parsec_isochrones.py; dashed PARSEC overlay on HR gallery and scrolly age steps.',
      },
    ],
  },
  {
    id: 'phase-iii',
    label: 'Phase III',
    title: 'Validation',
    summary:
      'Compare Q-value candidates to Malofeeva IR binaries, WOCS RV binaries, and Gaia astrometric anomalies; quantify completeness.',
    status: 'upcoming',
    explorations: [
      {
        id: 'q-demo',
        title: 'Q-value arithmetic',
        summary: 'Interactive Pyodide demo for the equal-mass binary track offset heuristic.',
        homeHref: '#code',
      },
      {
        id: 'malofeeva-layer',
        title: 'Malofeeva IR sample',
        summary: '553 stars with Gaia+WISE pseudocolors — primary external check on B−V completeness.',
        homeHref: '#data',
        stat: '553 stars',
      },
      {
        id: 'wocs-truth',
        title: 'WOCS RV truth set',
        summary: '118 matched spectroscopic/rotation targets for gold-standard binary confirmation.',
        stat: '118 matched',
      },
      {
        id: 'questions',
        title: 'Open validation questions',
        summary: 'Which Midas candidates confirm in Malofeeva, WOCS RV, or Gaia astrometry?',
        homeHref: '#roadmap',
      },
    ],
    tasks: [
      {
        id: 'q-malofeeva',
        title: 'Join Q-value candidates to Malofeeva TID diagram',
        status: 'planned',
        detail: 'Confusion matrix for photometric vs. IR two-index binary detection.',
      },
      {
        id: 'wocs-rv',
        title: 'Cross-match WOCS spectroscopic binaries to Midas IDs',
        status: 'planned',
        detail: 'Gold-standard RV truth set for completeness estimates.',
      },
      {
        id: 'gaia-astro',
        title: 'Gaia RUWE / astrometric anomaly screen',
        status: 'planned',
        detail: 'Flag unresolved astrometric binaries independent of B−V offset.',
      },
      {
        id: 'roc',
        title: 'ROC curves & completeness / contamination stats',
        status: 'planned',
        detail: 'Bootstrap validation framework with magnitude bins.',
      },
      {
        id: 'q-calibrate',
        title: 'Q-value threshold calibration notebook',
        status: 'planned',
        detail: 'Tune ΔM_V and B−V deviation cuts against external truth sets.',
      },
      {
        id: 'ir-fetch',
        title: '2MASS + AllWISE field photometry cache',
        status: 'planned',
        detail: 'Cone-fetch near-IR colors for independent binary diagrams.',
      },
    ],
  },
  {
    id: 'phase-iv',
    label: 'Phase IV',
    title: 'Synthesis',
    summary:
      'Answer targeted questions on binary fraction vs. mass, white dwarf membership, and method limits; prepare manuscript or data release.',
    status: 'upcoming',
    explorations: [
      {
        id: 'binary-fraction',
        title: 'Binary fraction vs. mass',
        summary: 'Join validated samples without double-counting overlapping detections.',
      },
      {
        id: 'method-paper',
        title: 'Methods comparison',
        summary: 'B−V isochrone vs. Gaia+IR diagnostics in the Gaia era — where each technique wins.',
      },
      {
        id: 'wd',
        title: 'White dwarf candidates',
        summary: 'Rubin et al. candidates cross-checked with Gaia DR4 astrometry.',
      },
      {
        id: 'release',
        title: 'Public data release',
        summary: 'Reproducible scripts, processed tables, and a methods-focused write-up.',
      },
    ],
    tasks: [
      {
        id: 'binary-fraction',
        title: 'Binary fraction vs. mass (deduplicated catalogs)',
        status: 'planned',
        detail: 'Join all validated samples without double-counting overlapping detections.',
      },
      {
        id: 'method-compare',
        title: 'B−V isochrone vs. Gaia+IR method comparison write-up',
        status: 'planned',
        detail: 'Quantify where each technique wins or misses low mass-ratio pairs.',
      },
      {
        id: 'wd-check',
        title: 'White dwarf candidate Gaia DR4 astrometry check',
        status: 'planned',
        detail: 'Ingest Rubin et al. candidates after core binary validation.',
      },
      {
        id: 'release',
        title: 'Manuscript or public data release',
        status: 'planned',
        detail: 'Methods-focused paper with reproducible scripts and processed tables.',
      },
    ],
  },
];

export function getPhaseById(phaseId: string): RoadmapPhase | undefined {
  return ROADMAP_PHASES.find((p) => p.id === phaseId);
}

export function phaseProgress(phase: RoadmapPhase): number {
  if (phase.tasks.length === 0) return 0;
  const score = phase.tasks.reduce((sum, task) => {
    if (task.status === 'done') return sum + 1;
    if (task.status === 'in_progress') return sum + 0.5;
    return sum;
  }, 0);
  return Math.round((score / phase.tasks.length) * 100);
}

export function overallProgress(phases: RoadmapPhase[]): number {
  const allTasks = phases.flatMap((p) => p.tasks);
  if (allTasks.length === 0) return 0;
  const score = allTasks.reduce((sum, task) => {
    if (task.status === 'done') return sum + 1;
    if (task.status === 'in_progress') return sum + 0.5;
    return sum;
  }, 0);
  return Math.round((score / allTasks.length) * 100);
}

export function countTasksByStatus(phases: RoadmapPhase[]): Record<WorkStatus, number> {
  const counts: Record<WorkStatus, number> = { done: 0, in_progress: 0, planned: 0 };
  for (const phase of phases) {
    for (const task of phase.tasks) {
      counts[task.status] += 1;
    }
  }
  return counts;
}
