const PHASES = [
  {
    num: 'Phase I',
    title: 'Archaeology & reproducibility',
    body: 'Document legacy photometry provenance, port pipelines to Python 3, reproduce Excel singles/binaries counts, publish this site.',
  },
  {
    num: 'Phase II',
    title: 'Gaia integration',
    body: 'Cross-match all Midas stars to Gaia DR3; replace Jones–Prosser membership with Cantat-Gaudin probabilities; apply reddening corrections.',
  },
  {
    num: 'Phase III',
    title: 'Validation',
    body: 'Compare Q-value candidates to Malofeeva IR binaries, WOCS RV binaries, and Gaia astrometric anomalies; quantify completeness.',
  },
  {
    num: 'Phase IV',
    title: 'Synthesis',
    body: 'Answer targeted questions on binary fraction vs. mass, white dwarf membership, and method limits; prepare manuscript or data release.',
  },
];

export function PhaseTimeline() {
  return (
    <div className="phases">
      {PHASES.map((p) => (
        <article key={p.num} className="phase-card">
          <div className="phase-card__num">{p.num}</div>
          <h4>{p.title}</h4>
          <p>{p.body}</p>
        </article>
      ))}
    </div>
  );
}

const TOOLS: { name: string; exists: string; build: string }[] = [
  { name: 'Legacy Midas CSV / Excel', exists: '✓ Original data & formulas', build: '—' },
  { name: 'Yonsei–Yale isochrones', exists: '✓ ISO.csv in repo', build: 'PARSEC/MIST comparison' },
  { name: 'Jones–Prosser membership', exists: '✓ Members.csv', build: 'Gaia replacement layer' },
  { name: 'Q-value binary heuristic', exists: '✓ Midas.py logic', build: 'Statistical calibration' },
  { name: 'Gaia cross-match', exists: 'astroquery recipes', build: 'Automated pipeline script' },
  { name: 'Malofeeva binary catalog', exists: 'Published tables', build: 'Ingest + join to Midas IDs' },
  { name: 'Interactive HR / sky maps', exists: '✓ This website', build: 'Live Gaia overlay' },
  { name: 'Runnable notebooks', exists: 'Pyodide demos', build: 'Jupyter in research/' },
  { name: 'CI / Pages deploy', exists: 'GitHub + GitLab workflows', build: 'Custom domain (optional)' },
];

export function ToolsMatrix() {
  return (
    <div className="tools-grid">
      <div className="tools-grid__head">Component</div>
      <div className="tools-grid__head">Exists today</div>
      <div className="tools-grid__head">To build</div>
      {TOOLS.flatMap((row) => [
        <div key={`${row.name}-n`} className="tools-grid__cell">
          {row.name}
        </div>,
        <div key={`${row.name}-e`} className="tools-grid__cell tools-grid__cell--exists">
          {row.exists}
        </div>,
        <div key={`${row.name}-b`} className="tools-grid__cell tools-grid__cell--build">
          {row.build}
        </div>,
      ])}
    </div>
  );
}
