import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { PRISM, PRISM_DOCS, PRISM_LINKS, PRISM_MODULE, GITHUB_REPO } from '../data/prism';

function VerdictBadge({ verdict }: { verdict: 'recommended' | 'future' | 'not-recommended' }) {
  const labels = {
    recommended: 'Recommended',
    future: 'Future path',
    'not-recommended': 'Not recommended',
  };
  return <span className={`prism-verdict prism-verdict--${verdict}`}>{labels[verdict]}</span>;
}

export function PrismPage() {
  const {
    acronym,
    name,
    tagline,
    lede,
    benchmark,
    coverage,
    fit,
    approach,
    comparisons,
    valueAdds,
    software,
    limitations,
    roadmap,
  } = PRISM;

  return (
    <>
      <Header />
      <main className="prism-page">
        <div className="prism-page__hero section">
          <p className="section__label">Phase V · Proposed detector</p>
          <h1 className="prism-page__title">
            {acronym}
            <span className="prism-page__subtitle">{name}</span>
          </h1>
          <p className="prism-page__tagline">{tagline}</p>
          <p className="prism-page__lede lead">{lede}</p>
        </div>

        <section className="section section--rule" aria-label="M34 benchmark">
          <h2 className="section__subhead">M34 benchmark</h2>
          <p className="section__prose">
            {benchmark.n} Cantat-Gaudin members · truth proxy: {benchmark.truthSet} · best
            threshold = {benchmark.bestThreshold}
          </p>
          <div className="prism-benchmark">
            <table className="prism-table">
              <thead>
                <tr>
                  <th scope="col">Method</th>
                  <th scope="col">Precision</th>
                  <th scope="col">Recall</th>
                  <th scope="col">F1</th>
                </tr>
              </thead>
              <tbody>
                <tr className="prism-table__highlight">
                  <th scope="row">Prism (tuned)</th>
                  <td>{benchmark.prism.precision.toFixed(3)}</td>
                  <td>{benchmark.prism.recall.toFixed(3)}</td>
                  <td>
                    <strong>{benchmark.prism.f1.toFixed(3)}</strong>
                  </td>
                </tr>
                <tr>
                  <th scope="row">
                    Legacy Q ∈ ({benchmark.qValue.qRange[0]}, {benchmark.qValue.qRange[1]}]
                  </th>
                  <td>{benchmark.qValue.precision.toFixed(3)}</td>
                  <td>{benchmark.qValue.recall.toFixed(3)}</td>
                  <td>{benchmark.qValue.f1.toFixed(3)}</td>
                </tr>
                <tr>
                  <th scope="row">Prism (default z ≥ {fit.scoreThresholdDefault})</th>
                  <td>{benchmark.defaultThreshold.precision.toFixed(3)}</td>
                  <td>{benchmark.defaultThreshold.recall.toFixed(3)}</td>
                  <td>{benchmark.defaultThreshold.f1.toFixed(3)}</td>
                </tr>
              </tbody>
            </table>
            <dl className="findings-glance prism-benchmark__meta">
              <div className="findings-glance__item">
                <dt>Dual-plane coverage</dt>
                <dd>
                  <span className="findings-glance__value">
                    {coverage.nCgDualPlane} / {coverage.nCgMembers}
                  </span>
                  <span className="findings-glance__detail">CG members with W2−BP</span>
                </dd>
              </div>
              <div className="findings-glance__item">
                <dt>Sequence training</dt>
                <dd>
                  <span className="findings-glance__value">{fit.nTrainOptical}</span>
                  <span className="findings-glance__detail">optical · {fit.nTrainIr} IR (σ-clipped)</span>
                </dd>
              </div>
            </dl>
          </div>
        </section>

        <section className="section section--rule" id="approach">
          <h2 className="section__subhead">Approach</h2>
          <div className="prism-planes" aria-hidden="true">
            <div className="prism-planes__plane">
              <p className="prism-planes__label">Optical plane</p>
              <p className="prism-planes__axes">BP − RP vs G</p>
              <p className="prism-planes__note">Gaia CMD residual</p>
            </div>
            <div className="prism-planes__fuse">⊕</div>
            <div className="prism-planes__plane">
              <p className="prism-planes__label">IR plane</p>
              <p className="prism-planes__axes">W2 − BP vs BP − RP</p>
              <p className="prism-planes__note">IR pseudocolor residual</p>
            </div>
            <div className="prism-planes__fuse">→</div>
            <div className="prism-planes__plane prism-planes__plane--score">
              <p className="prism-planes__label">Prism score</p>
              <p className="prism-planes__axes">hypot(z_opt⁺, z_ir⁺)</p>
            </div>
          </div>
          {approach.map((block) => (
            <article key={block.id} id={block.id} className="prism-section">
              <h3 className="prism-section__title">{block.title}</h3>
              {block.paragraphs.map((p) => (
                <p key={p.slice(0, 40)} className="section__prose">
                  {p}
                </p>
              ))}
              {block.bullets && (
                <ul className="findings-section__list section__prose">
                  {block.bullets.map((b) => (
                    <li key={b.slice(0, 30)}>{b}</li>
                  ))}
                </ul>
              )}
            </article>
          ))}
        </section>

        <section className="section section--rule" id="compare">
          <h2 className="section__subhead">How Prism differs from other methods</h2>
          <p className="section__prose">
            Not a catalog union — a single anomaly score built from two photometric planes. Compared
            to the detectors already in the Project Midas pipeline:
          </p>
          <div className="prism-table-wrap">
            <table className="prism-table prism-table--wide">
              <thead>
                <tr>
                  <th scope="col">Method</th>
                  <th scope="col">Era</th>
                  <th scope="col">Planes</th>
                  <th scope="col">Training</th>
                  <th scope="col">Role</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((row) => (
                  <tr
                    key={row.id}
                    className={row.id === 'prism' ? 'prism-table__highlight' : undefined}
                  >
                    <th scope="row">{row.name}</th>
                    <td>{row.era}</td>
                    <td>{row.planes}</td>
                    <td>{row.training}</td>
                    <td>{row.role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="findings-section__link">
            <a href={PRISM_LINKS.compare}>See channel overlap on Compare</a>
            {' · '}
            <a href={PRISM_LINKS.findings}>Phase I–IV findings</a>
          </p>
        </section>

        <section className="section section--rule" id="value">
          <h2 className="section__subhead">What Prism adds</h2>
          <ul className="prism-value-list">
            {valueAdds.map(({ title, body }) => (
              <li key={title} className="prism-value-list__item">
                <h3>{title}</h3>
                <p>{body}</p>
              </li>
            ))}
          </ul>
        </section>

        <section className="section section--rule" id="software">
          <h2 className="section__subhead">Software path: own library vs Astropy</h2>
          <p className="section__prose">
            Prism should be a <strong>small, installable Python package</strong> — not a patch to{' '}
            <code>astropy</code> core. Cluster-specific binary heuristics with Gaia+WISE join logic
            are out of scope for core Astropy; an affiliated package is realistic only after
            cross-cluster validation and a stable API.
          </p>
          <div className="prism-software">
            {software.map((opt) => (
              <article key={opt.id} className={`prism-software__card prism-software__card--${opt.verdict}`}>
                <div className="prism-software__head">
                  <h3>{opt.title}</h3>
                  <VerdictBadge verdict={opt.verdict} />
                </div>
                <p>{opt.summary}</p>
                <div className="prism-software__cols">
                  <div>
                    <h4>Pros</h4>
                    <ul>
                      {opt.pros.map((p) => (
                        <li key={p.slice(0, 24)}>{p}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4>Cons</h4>
                    <ul>
                      {opt.cons.map((c) => (
                        <li key={c.slice(0, 24)}>{c}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </article>
            ))}
          </div>
          <p className="section__prose prism-software__rec">
            <strong>Recommendation:</strong> extract <code>cluster-prism</code> (working name) from{' '}
            <code>research/midas/prism.py</code> — numpy core, optional astropy for coordinates,
            pytest + Zenodo DOI. Revisit Astropy Affiliated status after Pleiades/Hyades benchmarks.
          </p>
        </section>

        <section className="section section--rule" id="try">
          <h2 className="section__subhead">Try it</h2>
          <pre className="prism-code">
            <code>{`cd research && source .venv/bin/activate
python scripts/merge_ir_photometry.py   # if needed
python scripts/validate_prism.py
python scripts/build_web_prism.py       # refresh site JSON`}</code>
          </pre>
          <p className="findings-section__link">
            <a href={PRISM_MODULE}>midas/prism.py</a>
            {' · '}
            <a href={PRISM_DOCS}>PRISM_DETECTOR.md</a>
            {' · '}
            <a href={PRISM_LINKS.validateScript}>validate_prism.py</a>
            {' · '}
            <a href={GITHUB_REPO}>GitHub</a>
          </p>
        </section>

        <section className="prism-page__closing section section--rule">
          <h2 className="section__subhead">Limitations</h2>
          <ul className="findings-section__list section__prose">
            {limitations.map((item) => (
              <li key={item.slice(0, 30)}>{item}</li>
            ))}
          </ul>
          <h2 className="section__subhead">Roadmap</h2>
          <ul className="findings-section__list section__prose">
            {roadmap.map((item) => (
              <li key={item.slice(0, 30)}>{item}</li>
            ))}
          </ul>
        </section>
      </main>
      <Footer />
    </>
  );
}

export default PrismPage;
