import wdData from '../data/wdCheckSummary.json';

const { meta, summary, candidates } = wdData;

const MEMBER_ROWS = candidates.filter(
  (c) => c.paperMember === 'yes' || c.paperMember === 'possible',
);

const VERDICT_CLASS: Record<string, string> = {
  cluster_astrometry: 'wd-verdict--cluster',
  partial_cluster: 'wd-verdict--partial',
  photometric_member: 'wd-verdict--photo',
  likely_field: 'wd-verdict--field',
  no_gaia: 'wd-verdict--none',
  not_wd: 'wd-verdict--not',
};

export function WhiteDwarfCheck() {
  return (
    <div className="wd-check">
      <h3 className="data-compare__subhead">Rubin et al. white dwarf candidates</h3>
      <p className="section__prose data-compare__intro">
        Rubin et al. (2008) photometrically selected 44 LAWDS candidates in the M34 field;
        17 were spectroscopically confirmed as DA WDs, with five at the cluster distance modulus
        (plus one possible double degenerate). We cross-match each candidate to our existing{' '}
        {meta.gaiaRelease} field catalog and compare parallax and proper motion to the Cantat-Gaudin
        member locus (median PM from {meta.nCandidates} candidates vs 263 CG stars on the join
        table).
      </p>

      <dl className="join-summary" aria-label="White dwarf check summary">
        <div className="join-summary__item">
          <dt>LAWDS candidates</dt>
          <dd>
            <span className="join-summary__value">{meta.nCandidates}</span>
            <span className="join-summary__detail">Table 2 (Rubin+ 2008)</span>
          </dd>
        </div>
        <div className="join-summary__item">
          <dt>Gaia matched (≤2″)</dt>
          <dd>
            <span className="join-summary__value">{summary.nGaiaMatched}</span>
            <span className="join-summary__detail">{meta.gaiaRelease} — many faint WDs lack clean matches</span>
          </dd>
        </div>
        <div className="join-summary__item">
          <dt>Paper cluster DA members</dt>
          <dd>
            <span className="join-summary__value">{summary.nPaperClusterMembers}</span>
            <span className="join-summary__detail">LAWDS 9, 15, 17, 20, S2 (+ S1 possible)</span>
          </dd>
        </div>
        <div className="join-summary__item">
          <dt>Gaia π + PM cluster match</dt>
          <dd>
            <span className="join-summary__value">{summary.nClusterAstrometry}</span>
            <span className="join-summary__detail">
              M34 (m−M)<sub>V</sub> ≈ {meta.m34DistMod} · π ≈ {(1000 / meta.m34DistancePc).toFixed(2)} mas
            </span>
          </dd>
        </div>
      </dl>

      <h4 className="wd-check__subhead">Paper cluster members vs Gaia DR3</h4>
      <div className="method-compare__table-wrap">
        <table className="method-compare__table wd-check__table">
          <caption className="visually-hidden">
            Rubin et al. cluster white dwarf candidates with Gaia astrometry
          </caption>
          <thead>
            <tr>
              <th scope="col">LAWDS</th>
              <th scope="col">Spec</th>
              <th scope="col">Paper</th>
              <th scope="col">(m−M)<sub>V</sub></th>
              <th scope="col">π (mas)</th>
              <th scope="col">ΔPM</th>
              <th scope="col">Gaia verdict</th>
            </tr>
          </thead>
          <tbody>
            {MEMBER_ROWS.map((row) => (
              <tr key={row.id}>
                <td>LAWDS {row.id}</td>
                <td>{row.specId}</td>
                <td>{row.paperMember}</td>
                <td>{row.distModV?.toFixed(2) ?? '—'}</td>
                <td>{row.parallax?.toFixed(2) ?? '—'}</td>
                <td>{row.pmOffset?.toFixed(2) ?? '—'}</td>
                <td>
                  <span className={`wd-verdict ${VERDICT_CLASS[row.verdict] ?? ''}`}>
                    {row.verdictLabel}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <details className="wd-check__details">
        <summary>All 44 LAWDS candidates</summary>
        <div className="method-compare__table-wrap">
          <table className="method-compare__table wd-check__table">
            <thead>
              <tr>
                <th scope="col">LAWDS</th>
                <th scope="col">V</th>
                <th scope="col">Spec</th>
                <th scope="col">Gaia</th>
                <th scope="col">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((row) => (
                <tr key={row.id}>
                  <td>LAWDS {row.id}</td>
                  <td>{row.vMag?.toFixed(2) ?? '—'}</td>
                  <td>{row.specId}</td>
                  <td>{row.gaiaId ? `${row.sepArcsec?.toFixed(1)}″` : '—'}</td>
                  <td>{row.verdictLabel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <p className="method-compare__source">
        Rubin et al. (2008, <a href="https://arxiv.org/abs/0805.3156">arXiv:0805.3156</a>) ·{' '}
        <code>validate_wd_check.py</code> on {meta.gaiaRelease} · DR4 refresh when available
      </p>
    </div>
  );
}
