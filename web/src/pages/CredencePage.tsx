import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { CREDENCE, CREDENCE_LINKS, GITHUB_REPO } from '../data/credence';
import m34Science from '../data/credenceM34Science.json';
import t1Pilot from '../data/credenceT1Pilot.json';
import { T0, T1 } from '../utils/tierLabel';

function VerdictBadge({ verdict }: { verdict: 'recommended' | 'future' | 'not-recommended' }) {
  const labels = {
    recommended: 'Recommended',
    future: 'Future path',
    'not-recommended': 'Not recommended',
  };
  return <span className={`credence-verdict credence-verdict--${verdict}`}>{labels[verdict]}</span>;
}

export function CredencePage() {
  const {
    name,
    tagline,
    lede,
    glance,
    vision,
    pipeline,
    design,
    dataScope,
    membership,
    infer,
    display,
    software,
    midasLink,
    limitations,
    roadmap,
  } = CREDENCE;

  const { benchmark, coverage, model, t0 } = infer;

  return (
    <>
      <Header />
      <main className="credence-page">
        <div className="credence-page__hero section" id="vision">
          <p className="section__label">Phase V · Ingest · Resolve · Infer · Display</p>
          <h1 className="credence-page__title">{name}</h1>
          <p className="credence-page__tagline">{tagline}</p>
          <p className="credence-page__lede lead">{lede}</p>
        </div>

        <section className="section section--rule" aria-label="At a glance">
          <h2 className="section__subhead">At a glance</h2>
          <dl className="findings-glance">
            {glance.map(({ label, value, detail }) => (
              <div key={label} className="findings-glance__item">
                <dt>{label}</dt>
                <dd>
                  <span className="findings-glance__value">{value}</span>
                  <span className="findings-glance__detail">{detail}</span>
                </dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="section section--rule">
          <h2 className="section__subhead">{vision.title}</h2>
          {vision.paragraphs.map((p) => (
            <p key={p.slice(0, 48)} className="section__prose">
              {p}
            </p>
          ))}
          <ul className="findings-section__list section__prose">
            {vision.bullets?.map((b) => (
              <li key={b.slice(0, 32)}>{b}</li>
            ))}
          </ul>
        </section>

        <section className="section section--rule" id="pipeline">
          <h2 className="section__subhead">{pipeline.title}</h2>
          {pipeline.paragraphs.map((p) => (
            <p key={p.slice(0, 48)} className="section__prose">
              {p}
            </p>
          ))}
          <div className="credence-flow" aria-hidden="true">
            {pipeline.steps.flatMap((step, i) => {
              const nodes = [];
              if (i > 0) {
                nodes.push(
                  <div key={`arrow-${step.id}`} className="credence-flow__arrow">
                    →
                  </div>,
                );
              }
              nodes.push(
                <div
                  key={step.id}
                  className={`credence-flow__step${i > 0 && i < 3 ? ' credence-flow__step--accent' : ''}`}
                >
                  <p className="credence-flow__label">{step.title.split(' · ')[0]}</p>
                  <p className="credence-flow__name">{step.title.split(' · ')[1] ?? step.title}</p>
                  <p className="credence-flow__note">{step.summary.slice(0, 48)}…</p>
                </div>,
              );
              return nodes;
            })}
          </div>
          {pipeline.steps.map((step) => (
            <article key={step.id} className="credence-section">
              <h3 className="credence-section__title">{step.title}</h3>
              <p className="section__prose">{step.summary}</p>
              <ul className="findings-section__list section__prose">
                {step.deliverables.map((d) => (
                  <li key={d.slice(0, 28)}>{d}</li>
                ))}
              </ul>
            </article>
          ))}
        </section>

        <section className="section section--rule" id="design">
          <h2 className="section__subhead">{design.title}</h2>
          <p className="section__prose">{design.lede}</p>
          <pre className="credence-code credence-diagram" aria-label="System diagram">
            <code>{design.diagram}</code>
          </pre>
          <div className="credence-design-grid">
            <article className="credence-section">
              <h3 className="credence-section__title">StarEntity (resolve output)</h3>
              <ul className="findings-section__list section__prose">
                {design.starEntity.map((line) => (
                  <li key={line.slice(0, 24)}>{line}</li>
                ))}
              </ul>
            </article>
            <article className="credence-section">
              <h3 className="credence-section__title">CredenceVector (infer output)</h3>
              <ul className="findings-section__list section__prose">
                {design.credenceVector.map((line) => (
                  <li key={line.slice(0, 24)}>{line}</li>
                ))}
              </ul>
            </article>
          </div>
          <article className="credence-section">
            <h3 className="credence-section__title">Storage layers</h3>
            <ul className="findings-section__list section__prose">
              {design.storage.map((line) => (
                <li key={line.slice(0, 24)}>{line}</li>
              ))}
            </ul>
          </article>
          <article className="credence-section">
            <h3 className="credence-section__title">M34 today → Credence target</h3>
            <ul className="findings-section__list section__prose">
              {design.m34Mapping.map((line) => (
                <li key={line.slice(0, 24)}>{line}</li>
              ))}
            </ul>
          </article>
          <p className="findings-section__link">
            <a href={CREDENCE_LINKS.architecture}>Full design doc (CREDENCE_ARCHITECTURE.md)</a>
            {' · '}
            <a href={CREDENCE_LINKS.mlStrategy}>ML data strategy</a>
            {' · '}
            <a href={CREDENCE_LINKS.docs}>CREDENCE.md</a>
          </p>

          <article className="credence-section" id="ml-plan">
            <h3 className="credence-section__title">{design.mlDataStrategy.title}</h3>
            <p className="section__prose">{design.mlDataStrategy.lede}</p>
            <div className="credence-table-wrap">
              <table className="credence-table credence-table--wide">
                <thead>
                  <tr>
                    <th scope="col">Approach</th>
                    <th scope="col">Verdict</th>
                    <th scope="col">Note</th>
                  </tr>
                </thead>
                <tbody>
                  {design.mlDataStrategy.verdicts.map((row) => (
                    <tr key={row.approach}>
                      <th scope="row">{row.approach}</th>
                      <td>{row.verdict}</td>
                      <td>{row.note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="section__prose">
              <strong>M34 today:</strong>
            </p>
            <ul className="findings-section__list section__prose">
              {design.mlDataStrategy.m34Today.map((line) => (
                <li key={line.slice(0, 28)}>{line}</li>
              ))}
            </ul>
            <p className="section__prose">
              <strong>Protocol ({T0}+):</strong>
            </p>
            <ul className="findings-section__list section__prose">
              {design.mlDataStrategy.protocol.map((line) => (
                <li key={line.slice(0, 28)}>{line}</li>
              ))}
            </ul>
          </article>

          <article className="credence-section">
            <h3 className="credence-section__title">{design.inferEngine.title}</h3>
            <p className="section__prose">{design.inferEngine.note}</p>
            <p className="section__prose">
              <strong>Architecture:</strong>
            </p>
            <ul className="findings-section__list section__prose">
              {design.inferEngine.architecture.map((line) => (
                <li key={line.slice(0, 28)}>{line}</li>
              ))}
            </ul>
            <p className="section__prose">
              <strong>Next:</strong>
            </p>
            <ul className="findings-section__list section__prose">
              {design.inferEngine.next.map((line) => (
                <li key={line.slice(0, 28)}>{line}</li>
              ))}
            </ul>
          </article>
        </section>

        <section className="section section--rule" id="data">
          <h2 className="section__subhead">{dataScope.title}</h2>
          {dataScope.paragraphs.map((p) => (
            <p key={p.slice(0, 48)} className="section__prose">
              {p}
            </p>
          ))}
          <div className="credence-table-wrap">
            <table className="credence-table credence-table--wide">
              <thead>
                <tr>
                  <th scope="col">Tier</th>
                  <th scope="col">Clusters</th>
                  <th scope="col">Stars (order of magnitude)</th>
                  <th scope="col">Modalities</th>
                  <th scope="col">Purpose</th>
                </tr>
              </thead>
              <tbody>
                {dataScope.tiers.map((tier) => (
                  <tr key={tier.id}>
                    <th scope="row">{tier.label}</th>
                    <td>{tier.clusters}</td>
                    <td>{tier.stars}</td>
                    <td>{tier.modalities}</td>
                    <td>{tier.purpose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="section__prose credence-storage-note">{dataScope.storageNote}</p>
        </section>

        <section className="section section--rule" id="membership">
          <h2 className="section__subhead">{membership.title}</h2>
          {membership.paragraphs.map((p) => (
            <p key={p.slice(0, 48)} className="section__prose">
              {p}
            </p>
          ))}
          <ul className="findings-section__list section__prose">
            {membership.bullets.map((b) => (
              <li key={b.slice(0, 32)}>{b}</li>
            ))}
          </ul>
        </section>

        <section className="section section--rule" id="infer">
          <h2 className="section__subhead">{infer.title}</h2>
          <p className="section__prose">{infer.note}</p>
          <div className="credence-planes" aria-hidden="true">
            <div className="credence-planes__plane">
              <p className="credence-planes__label">Gaia</p>
              <p className="credence-planes__axes">G · BP−RP · RUWE</p>
            </div>
            <div className="credence-planes__fuse">⊕</div>
            <div className="credence-planes__plane">
              <p className="credence-planes__label">WISE</p>
              <p className="credence-planes__axes">W2 − BP</p>
            </div>
            <div className="credence-planes__fuse">→</div>
            <div className="credence-planes__plane credence-planes__plane--score">
              <p className="credence-planes__label">Heads</p>
              <p className="credence-planes__axes">p_binary · p_cmd · p_ir · p_ruwe</p>
            </div>
          </div>
          <ul className="findings-section__list section__prose">
            {infer.planes.map((line) => (
              <li key={line.slice(0, 24)}>{line}</li>
            ))}
          </ul>
          <p className="section__prose">{infer.training}</p>

          <h3 className="credence-section__title">M34 benchmark</h3>
          <p className="section__prose">
            {benchmark.n} Cantat-Gaudin members · truth proxy: {benchmark.truthSet} · tuned threshold ={' '}
            {benchmark.bestThreshold}
          </p>
          <div className="credence-benchmark">
            <table className="credence-table">
              <thead>
                <tr>
                  <th scope="col">Method</th>
                  <th scope="col">Precision</th>
                  <th scope="col">Recall</th>
                  <th scope="col">F1</th>
                </tr>
              </thead>
              <tbody>
                <tr className="credence-table__highlight">
                  <th scope="row">Credence infer (tuned)</th>
                  <td>{benchmark.credence.precision.toFixed(3)}</td>
                  <td>{benchmark.credence.recall.toFixed(3)}</td>
                  <td>
                    <strong>{benchmark.credence.f1.toFixed(3)}</strong>
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
                  <th scope="row">Default p_binary ≥ {benchmark.defaultThreshold.threshold}</th>
                  <td>{benchmark.defaultThreshold.precision.toFixed(3)}</td>
                  <td>{benchmark.defaultThreshold.recall.toFixed(3)}</td>
                  <td>{benchmark.defaultThreshold.f1.toFixed(3)}</td>
                </tr>
              </tbody>
            </table>
            <dl className="findings-glance credence-benchmark__meta">
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
                <dt>Model training</dt>
                <dd>
                  <span className="findings-glance__value">{model.nTrain}</span>
                  <span className="findings-glance__detail">
                    train · {model.nVal} val · val F1 {model.valF1Last?.toFixed(2)}
                  </span>
                </dd>
              </div>
            </dl>
          </div>

          <h3 className="credence-section__title">{T1} pilot ingest &amp; v8-t1</h3>
          <p className="section__prose">
            Azure Batch pilot: {t1Pilot.ingest.pilotSucceeded}/{t1Pilot.ingest.pilotTotal} clusters ·{' '}
            {t1Pilot.ingest.memberRows.toLocaleString()} CG member rows in Blob Parquet. Full registry:{' '}
            {t1Pilot.ingest.fullRegistryClusters.toLocaleString()} clusters queued for scale ingest.
          </p>
          {typeof t1Pilot.model.headlineMeanDeltaF1 === 'number' && (
            <p className="section__prose">
              v8-t1 pretrained → frozen {T0} LOO headline mean ΔF1:{' '}
              <strong>{t1Pilot.model.headlineMeanDeltaF1 >= 0 ? '+' : ''}
              {t1Pilot.model.headlineMeanDeltaF1.toFixed(3)}</strong>
            </p>
          )}
          <p className="section__prose">
            <a href="/atlas">Open Credence Atlas</a> — {T1} pilot clusters when atlas bundle is built.
          </p>

          <h3 className="credence-section__title">{T0} cluster-held-out ({t0.meta.modelVersion})</h3>
          <p className="section__prose">{t0.meta.evalNote}</p>
          {typeof t0.meta.headlineMeanDeltaF1 === 'number' && (
            <p className="section__prose">
              Headline mean ΔF1 (3 Malofeeva folds):{' '}
              <strong className={t0.meta.headlineMeanDeltaF1 >= 0 ? 'credence-delta-pos' : undefined}>
                {t0.meta.headlineMeanDeltaF1 >= 0 ? '+' : ''}
                {t0.meta.headlineMeanDeltaF1.toFixed(3)}
              </strong>
              {typeof t0.meta.headlineBeatsBaseline === 'number' && (
                <> · {t0.meta.headlineBeatsBaseline}/3 folds beat all-positive baseline</>
              )}
              {typeof t0.meta.nestedOracleMeanDeltaF1 === 'number' && (
                <>
                  {' '}
                  · per-fold nested-oracle ceiling{' '}
                  {t0.meta.nestedOracleMeanDeltaF1 >= 0 ? '+' : ''}
                  {t0.meta.nestedOracleMeanDeltaF1.toFixed(3)}
                </>
              )}
            </p>
          )}
          {t0.defaultHoldout && (
            <p className="section__prose">
              Default holdout ({t0.defaultHoldout.clusterIds.join(', ')}): {t0.defaultHoldout.truthSet} ·
              n={t0.defaultHoldout.nTest} (n_pos={t0.defaultHoldout.nPos}) · F1@0.5={t0.defaultHoldout.f1.toFixed(3)}
              {typeof t0.defaultHoldout.specificity === 'number' && (
                <> · spec={t0.defaultHoldout.specificity.toFixed(3)}</>
              )}
              {typeof t0.defaultHoldout.f1AllPositiveBaseline === 'number' && (
                <> · all-pos baseline={t0.defaultHoldout.f1AllPositiveBaseline.toFixed(3)}</>
              )}
            </p>
          )}
          {t0.leaveOneClusterOut.length > 0 && (
            <div className="credence-table-wrap">
              <table className="credence-table credence-table--wide">
                <thead>
                  <tr>
                    <th scope="col">Held-out cluster</th>
                    <th scope="col">Truth proxy</th>
                    <th scope="col">n</th>
                    <th scope="col">n_pos</th>
                    <th scope="col">F1 @0.5</th>
                    <th scope="col">Spec</th>
                    <th scope="col">ΔF1</th>
                    <th scope="col">All-pos F1</th>
                    <th scope="col">Val-tuned F1</th>
                  </tr>
                </thead>
                <tbody>
                  {t0.leaveOneClusterOut.map((row) => (
                    <tr
                      key={row.clusterId}
                      className={
                        row.beatsAllPosBaseline
                          ? 'credence-table__beat-baseline'
                          : row.clusterId === 'ngc_1039'
                            ? 'credence-table__highlight'
                            : undefined
                      }
                    >
                      <th scope="row">{row.clusterName}</th>
                      <td>{row.truthSet}</td>
                      <td>{row.nTest}</td>
                      <td>{row.nPos ?? '—'}</td>
                      <td>{row.f1At05?.toFixed(3) ?? row.f1.toFixed(3)}</td>
                      <td>{row.specificity?.toFixed(3) ?? '—'}</td>
                      <td>
                        {typeof row.deltaF1 === 'number' ? (
                          <span className={row.deltaF1 >= 0 ? 'credence-delta-pos' : undefined}>
                            {row.deltaF1 >= 0 ? '+' : ''}
                            {row.deltaF1.toFixed(3)}
                          </span>
                        ) : (
                          '—'
                        )}
                        {row.headline === false && (
                          <span title="Non-headline tier (provisional or weak proxy)"> ·</span>
                        )}
                      </td>
                      <td>{row.f1AllPositiveBaseline?.toFixed(3) ?? '—'}</td>
                      <td>
                        {row.f1ValTuned?.toFixed(3) ?? '—'}
                        {row.beatsAllPosBaseline === false && (
                          <span title="Does not beat predict-all-positive baseline"> ≈ baseline</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="credence-eval-caveat">{t0.meta.evalNote}</p>
            </div>
          )}

          {m34Science.variants?.length > 0 && (
            <>
              <h4 className="credence-section__subtitle">M34 science holdout (ngc_1039)</h4>
              <p className="section__prose">
                Cluster-held-out on M34 with legacy Midas Q baseline (BVR pipeline, 108/108 mapped).
                {m34Science.bvr_coverage && (
                  <>
                    {' '}
                    Legacy BVR (bv0/mv0) available for {m34Science.bvr_coverage.n_with_legacy_bvr}/
                    {m34Science.bvr_coverage.n_eval} eval-universe stars — not yet in the neural feature
                    tensor.
                  </>
                )}
              </p>
              <div className="credence-table-wrap">
                <table className="credence-table credence-table--wide">
                  <thead>
                    <tr>
                      <th scope="col">Config</th>
                      <th scope="col">Label case</th>
                      <th scope="col">n_pos</th>
                      <th scope="col">Credence ΔF1</th>
                      <th scope="col">Legacy Q ΔF1</th>
                    </tr>
                  </thead>
                  <tbody>
                    {m34Science.variants.flatMap((variant) =>
                      Object.values(variant.label_cases).map((block) => (
                        <tr key={`${variant.variant}-${block.label_case}`}>
                          <td>{variant.variant}</td>
                          <td>({block.label_case})</td>
                          <td>
                            {block.n_pos}/{block.n}
                          </td>
                          <td>
                            <span
                              className={
                                block.delta_f1_credence >= 0 ? 'credence-delta-pos' : undefined
                              }
                            >
                              {block.delta_f1_credence >= 0 ? '+' : ''}
                              {block.delta_f1_credence.toFixed(3)}
                            </span>
                          </td>
                          <td>
                            {block.delta_f1_legacy_q >= 0 ? '+' : ''}
                            {block.delta_f1_legacy_q.toFixed(3)}
                          </td>
                        </tr>
                      )),
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
          <p className="findings-section__link">
            <a href="/atlas">Open Credence Atlas</a>
            {' · '}
            <a href={CREDENCE_LINKS.mlStrategy}>ML data strategy</a>
          </p>
          <p className="findings-section__link">
            <a href={CREDENCE_LINKS.module}>midas/credence/</a>
            {' · '}
            <a href={CREDENCE_LINKS.docs}>CREDENCE.md</a>
            {' · '}
            <a href={CREDENCE_LINKS.validateScript}>validate_credence.py</a>
          </p>
        </section>

        <section className="section section--rule" id="display">
          <h2 className="section__subhead">{display.title}</h2>
          {display.paragraphs.map((p) => (
            <p key={p.slice(0, 48)} className="section__prose">
              {p}
            </p>
          ))}
          <ul className="credence-value-list">
            {display.features.map(({ title, body }) => (
              <li key={title} className="credence-value-list__item">
                <h3>{title}</h3>
                <p>{body}</p>
              </li>
            ))}
          </ul>
          <article className="credence-section">
            <h3 className="credence-section__title">{display.database.title}</h3>
            {display.database.paragraphs.map((p) => (
              <p key={p.slice(0, 40)} className="section__prose">
                {p}
              </p>
            ))}
            <ul className="findings-section__list section__prose">
              {display.database.tables.map((t) => (
                <li key={t.slice(0, 20)}>
                  <code>{t.split(' — ')[0]}</code>
                  {t.includes(' — ') ? ` — ${t.split(' — ').slice(1).join(' — ')}` : ''}
                </li>
              ))}
            </ul>
          </article>
          <p className="section__prose">
            <a href="/atlas" className="hero__link">
              Open Credence Atlas
            </a>
            {' '}
            — {T0} clusters colored by <code>p_binary</code> (display step).
          </p>
        </section>

        <section className="section section--rule" id="software">
          <h2 className="section__subhead">Software path</h2>
          <div className="credence-software">
            {software.map((opt) => (
              <article
                key={opt.id}
                className={`credence-software__card credence-software__card--${opt.verdict}`}
              >
                <div className="credence-software__head">
                  <h3>{opt.title}</h3>
                  <VerdictBadge verdict={opt.verdict} />
                </div>
                <p>{opt.summary}</p>
                <div className="credence-software__cols">
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
        </section>

        <section className="section section--rule">
          <h2 className="section__subhead">{midasLink.title}</h2>
          {midasLink.paragraphs.map((p) => (
            <p key={p.slice(0, 48)} className="section__prose">
              {p}
            </p>
          ))}
          <p className="findings-section__link">
            <a href={CREDENCE_LINKS.findings}>Midas Continued findings</a>
            {' · '}
            <a href={CREDENCE_LINKS.data}>M34 data explorer</a>
            {' · '}
            <a href={CREDENCE_LINKS.compare}>Catalog comparison</a>
            {' · '}
            <a href={GITHUB_REPO}>GitHub</a>
          </p>
        </section>

        <section className="section section--rule" id="try">
          <h2 className="section__subhead">Run the M34 pipeline</h2>
          <pre className="credence-code">
            <code>{`cd research && source .venv/bin/activate
python scripts/cross_match.py          # resolve
python scripts/merge_ir_photometry.py  # ingest IR
python scripts/train_credence.py       # train (optional)
python scripts/validate_credence.py    # infer + benchmark
python scripts/build_web_all.py        # display JSON`}</code>
          </pre>
        </section>

        <section className="credence-page__closing section section--rule" id="roadmap">
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

export default CredencePage;
