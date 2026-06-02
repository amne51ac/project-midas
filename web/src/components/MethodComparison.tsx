import synthesis from '../data/synthesisSummary.json';
import { MethodCompareDiagram } from './MethodCompareDiagram';
import { WhiteDwarfCheck } from './WhiteDwarfCheck';

const { meta, overall, channels, overlap, byMass } = synthesis;

const MASS_CHANNELS = [
  { id: 'q' as const, label: 'Q-value', color: 'var(--accent)' },
  { id: 'malofeeva' as const, label: 'Malofeeva IR', color: '#c9a227' },
  { id: 'union' as const, label: 'Union', color: 'var(--ink-muted)' },
];

function pct(n: number, total: number): string {
  if (total === 0) return '0%';
  return `${Math.round((100 * n) / total)}%`;
}

export function MethodComparison() {
  const maxChannel = Math.max(...channels.map((c) => c.count), 1);

  return (
    <div className="method-compare">
      <h3 className="data-compare__subhead">Phase IV — method overlap</h3>
      <p className="section__prose data-compare__intro">
        On {meta.nCgMembers} Cantat-Gaudin members (P ≥ 0.7), each binary channel flags stars
        independently. The <strong>union</strong> counts a star once if any channel fires —{' '}
        {overall.nBinaryUnion} stars ({pct(overall.nBinaryUnion, overall.n)}), not the sum of
        channel hits. B−V isochrone offset (Q) and Gaia+IR colors (Malofeeva) overlap on{' '}
        {overlap.find((r) => r.label.startsWith('Q ∩'))?.count ?? 47} stars but disagree on most
        candidates.
      </p>

      <div className="compare-bars" role="img" aria-label="Binary channel hit counts on CG members">
        {channels.map((ch) => (
          <div key={ch.id} className="compare-row">
            <span>{ch.label}</span>
            <div className="compare-row__bar-wrap">
              <div
                className="compare-row__bar compare-row__bar--channel"
                data-channel={ch.id}
                style={{ width: `${(ch.count / maxChannel) * 100}%` }}
              />
            </div>
            <span>
              {ch.count}{' '}
              <span className="method-compare__pct">({pct(ch.count, overall.n)})</span>
            </span>
          </div>
        ))}
      </div>

      <h3 className="data-compare__subhead">Q vs Malofeeva (exclusive sets)</h3>
      <p className="section__prose data-compare__intro">
        These rows are mutually exclusive partitions of the CG member sample — useful for comparing
        photometric track offset vs IR pseudocolor without double-counting.
      </p>
      <dl className="join-summary" aria-label="Q and Malofeeva overlap on CG members">
        {overlap.slice(0, 6).map(({ label, count }) => (
          <div key={label} className="join-summary__item">
            <dt>{label}</dt>
            <dd>
              <span className="join-summary__value">{count}</span>
              <span className="join-summary__detail">{pct(count, overall.n)} of members</span>
            </dd>
          </div>
        ))}
      </dl>

      <h3 className="data-compare__subhead">W2−BP vs B−V (same axes as Malofeeva)</h3>
      <p className="section__prose data-compare__intro">
        Gaia BP and AllWISE W2 on each Midas row define the IR pseudocolor Malofeeva et al. used
        independently of the B−V isochrone track. Toggle layers to see where photometric Q-value
        picks land relative to IR-flagged members — most Malofeeva-only stars sit in W2−BP space
        without a high Q-value.
      </p>
      <MethodCompareDiagram />

      <h3 className="data-compare__subhead">Binary fraction vs. mass</h3>
      <p className="section__prose data-compare__intro">
        Bootstrap 95% CI on f(binary) in six mass bins (YY {meta.ageGyr} Gyr isochrone, E(B−V) ={' '}
        {meta.ebv}). Malofeeva dominates every bin; Q-value fraction falls toward higher mass.
      </p>
      <div className="method-compare__table-wrap">
        <table className="method-compare__table">
          <caption className="visually-hidden">
            Binary fraction by stellar mass for Q, Malofeeva, and union channels
          </caption>
          <thead>
            <tr>
              <th scope="col">M☉ bin</th>
              <th scope="col">n</th>
              {MASS_CHANNELS.map((ch) => (
                <th key={ch.id} scope="col">
                  {ch.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {byMass.union.map((bin, i) => (
              <tr key={`${bin.massLo}-${bin.massHi}`}>
                <td>
                  {bin.massLo.toFixed(2)}–{bin.massHi.toFixed(2)}
                </td>
                <td>{bin.n}</td>
                {MASS_CHANNELS.map((ch) => {
                  const row = byMass[ch.id][i];
                  if (!row) return <td key={ch.id}>—</td>;
                  const ci =
                    row.ciLo != null && row.ciHi != null
                      ? ` [${row.ciLo.toFixed(2)}, ${row.ciHi.toFixed(2)}]`
                      : '';
                  return (
                    <td key={ch.id}>
                      {row.fraction.toFixed(2)}
                      {ci}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="method-compare__source">
        From <code>run_phase4_synthesis.py</code> on CG members · regenerate via{' '}
        <code>python scripts/build_web_synthesis.py</code>
      </p>

      <WhiteDwarfCheck />
    </div>
  );
}
