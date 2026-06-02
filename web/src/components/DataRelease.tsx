import { repoBlobUrl, REPO_URL } from '../data/toolsInventory';

const STAGES = [
  {
    name: 'Core (Phases I–II)',
    command: 'python scripts/run_reproduction.py --stage core',
    outputs: ['m34_join.csv', 'midas_pipeline.csv'],
  },
  {
    name: 'Validation (Phase III)',
    command: 'python scripts/run_reproduction.py --stage phase3',
    outputs: ['validation_summary.json'],
  },
  {
    name: 'Synthesis (Phase IV)',
    command: 'python scripts/run_reproduction.py --stage phase4',
    outputs: ['synthesis_summary.json', 'm34_join_ir.csv', 'wd_check_summary.json'],
  },
  {
    name: 'Website JSON',
    command: 'python scripts/build_web_all.py',
    outputs: ['m34_sample.json', 'synthesisSummary.json', 'wdCheckSummary.json'],
  },
] as const;

const WEB_ARTIFACTS = [
  { label: 'HR sample + history', path: 'web/src/data/m34_sample.json' },
  { label: 'Catalog explorer layers', path: 'web/src/data/m34_catalogs.json' },
  { label: 'Method compare stats', path: 'web/src/data/synthesisSummary.json' },
  { label: 'W2−BP diagram points', path: 'web/src/data/methodCompareDiagram.json' },
  { label: 'White dwarf check', path: 'web/src/data/wdCheckSummary.json' },
];

export function DataRelease() {
  return (
    <section className="data-release">
      <h3 className="tools-category__title">Public data release</h3>
      <p className="tools-category__summary">
        Phase IV packages the full pipeline for reproduction. Processed CSVs stay local
        (gitignored); this repository ships scripts, documentation, and web-ready JSON
        summaries checked into <code>web/src/data/</code>.
      </p>

      <div className="data-release__links">
        <a href={repoBlobUrl('research/REPRODUCTION.md')}>REPRODUCTION.md</a>
        <span aria-hidden> · </span>
        <a href={`${REPO_URL}/blob/main/CITATION.cff`}>CITATION.cff</a>
        <span aria-hidden> · </span>
        <a href={repoBlobUrl('research/DATA_DICTIONARY.md')}>Data dictionary</a>
      </div>

      <h4 className="data-release__subhead">Pipeline stages</h4>
      <div className="method-compare__table-wrap">
        <table className="method-compare__table data-release__table">
          <thead>
            <tr>
              <th scope="col">Stage</th>
              <th scope="col">Command</th>
              <th scope="col">Key outputs</th>
            </tr>
          </thead>
          <tbody>
            {STAGES.map((s) => (
              <tr key={s.name}>
                <td>{s.name}</td>
                <td>
                  <code className="data-release__cmd">{s.command}</code>
                </td>
                <td>{s.outputs.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="section__prose data-compare__intro">
        Full end-to-end run (requires raw Midas CSVs + network for first-time catalog fetch):{' '}
        <code>python scripts/run_reproduction.py --stage all</code> from{' '}
        <code>research/</code>. Then <code>cd ../web && npm run build</code> to refresh the
        public site.
      </p>

      <h4 className="data-release__subhead">Checked-in web artifacts</h4>
      <ul className="data-release__artifact-list">
        {WEB_ARTIFACTS.map((a) => (
          <li key={a.path}>
            <a href={repoBlobUrl(a.path)}>{a.label}</a>
          </li>
        ))}
      </ul>
    </section>
  );
}
