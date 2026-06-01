/** Catalog footprint sizes and Midas join overlap — Phase I & II milestones on the home page. */

const CATALOG_SIZES = [
  { name: 'Midas photometry (join sample)', count: 3760, note: 'Deep BVR(I); 3,760 after B-band filter' },
  { name: 'Gaia DR3 field (0.5° cone)', count: 15211, note: 'gaia_m34.csv — background + cluster' },
  { name: 'Cantat-Gaudin UPMASK', count: 555, note: 'Probabilistic members, NGC 1039' },
  { name: 'Malofeeva IR binaries', count: 553, note: 'Gaia + WISE two-index sample' },
  { name: 'WOCS rot + RV targets', count: 120, note: 'Meibom et al. (2011) table 2' },
  { name: 'Jones & Prosser (1996)', count: 630, note: 'Legacy proper-motion membership' },
] as const;

const JOIN_OVERLAP = [
  { label: 'Gaia DR3 matched', value: '3,738', detail: '99.4% of Midas rows' },
  { label: 'Cantat-Gaudin (P ≥ 0.7)', value: '263', detail: 'High-confidence members' },
  { label: 'Malofeeva overlap', value: '248', detail: 'IR binary flags on join row' },
  { label: 'WOCS overlap', value: '118', detail: '120 VizieR targets; 2 outside B sample' },
  { label: 'Jones–Prosser overlap', value: '222', detail: 'Legacy PM membership codes' },
  { label: 'Excel singles / binaries', value: '187 / 171', detail: 'Control sheet via midas/excel.py' },
] as const;

export function DataComparison() {
  const max = Math.max(...CATALOG_SIZES.map((d) => d.count));

  return (
    <div className="data-compare">
      <h3 className="data-compare__subhead">Catalog footprints</h3>
      <p className="section__prose data-compare__intro">
        Each survey covers a different slice of M34. Bar lengths show raw catalog size — not unique
        stars, since the same object appears in multiple tables.
      </p>
      <div className="compare-bars" role="img" aria-label="Catalog size comparison">
        {CATALOG_SIZES.map((d) => (
          <div key={d.name} className="compare-row">
            <span title={d.note}>{d.name}</span>
            <div className="compare-row__bar-wrap">
              <div
                className="compare-row__bar"
                style={{ width: `${(d.count / max) * 100}%` }}
              />
            </div>
            <span>{d.count.toLocaleString()}</span>
          </div>
        ))}
      </div>

      <h3 className="data-compare__subhead">Midas join overlap</h3>
      <p className="section__prose data-compare__intro">
        <code>m34_join.csv</code> has one row per Midas star. Cross-match attaches Gaia IDs and
        catalog flags without double-counting — a star in Malofeeva, WOCS, and Excel is still a
        single row. Phase III validation compares set overlap, not the sum of catalog sizes.
      </p>
      <dl className="join-summary" aria-label="Join table overlap statistics">
        {JOIN_OVERLAP.map(({ label, value, detail }) => (
          <div key={label} className="join-summary__item">
            <dt>{label}</dt>
            <dd>
              <span className="join-summary__value">{value}</span>
              <span className="join-summary__detail">{detail}</span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
