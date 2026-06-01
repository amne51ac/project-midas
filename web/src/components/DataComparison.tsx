const DATASETS = [
  { name: 'Midas photometry', count: 5749, note: 'Deep BVR(I), legacy survey' },
  { name: 'Jones & Prosser (1996)', count: 630, note: 'Proper-motion membership' },
  { name: 'Cantat-Gaudin / Gaia', count: 711, note: 'Probabilistic DR2 members' },
  { name: 'Malofeev et al. (2023)', count: 553, note: 'Binary-sensitive IR sample' },
  { name: 'WOCS light curves', count: 5656, note: 'V-band time series' },
  { name: 'Gaia DR3 (field)', count: 12000, note: 'Approx. sources in 0.5° cone' },
];

export function DataComparison() {
  const max = Math.max(...DATASETS.map((d) => d.count));

  return (
    <div className="compare-bars" role="img" aria-label="Catalog size comparison">
      {DATASETS.map((d) => (
        <div key={d.name} className="compare-row">
          <span>{d.name}</span>
          <div className="compare-row__bar-wrap">
            <div
              className="compare-row__bar"
              style={{ width: `${(d.count / max) * 100}%` }}
            />
          </div>
          <span>{d.count.toLocaleString()}</span>
        </div>
      ))}
      <p style={{ fontSize: '0.85rem', color: 'var(--ink-faint)', marginTop: '1.5rem' }}>
        Counts are order-of-magnitude references from published catalogs; overlap is substantial.
        Project Midas aims to cross-match these explicitly in the research pipeline.
      </p>
    </div>
  );
}
