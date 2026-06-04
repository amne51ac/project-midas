import { useEffect, useMemo, useState } from 'react';
import { ConstellationFinder } from '../components/ConstellationFinder';
import { SkyImagery } from '../components/SkyImagery';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { HRExplainer } from '../components/HRExplainer';
import { HRDiagram, type HRDiagramMode } from '../components/HRDiagram';
import { HistoryTimeline } from '../components/HistoryTimeline';
import { DataExplorer } from '../components/DataExplorer';
import { DataComparison } from '../components/DataComparison';
import { MethodComparison } from '../components/MethodComparison';
import catalogs from '../data/m34_catalogs.json';
import type { CatalogBundle } from '../data/catalogTypes';
import { CodeDemoGallery } from '../components/CodeRunner';
import { CODE_DEMOS } from '../data/codeDemos';
import { useScrolly } from '../hooks/useScrolly';
import dataset from '../data/m34_sample.json';
import { ISOCHRONE_AGES, SCROLLY_COMPARE_AGES } from '../data/isochrones';
import { IsochroneExplorer } from '../components/IsochroneExplorer';
import type { DatasetMeta } from '../data/types';

const data = dataset as DatasetMeta;
const catalogBundle = catalogs as CatalogBundle;

const HR_STEPS = [
  {
    title: 'Every star has a color and a brightness',
    body: 'Photometry measures how much light arrives in each filter. The color index B−V compares blue and visual flux: smaller B−V means a hotter, bluer star. Apparent magnitude V tells you how bright the star looks from Earth — but not how luminous it truly is.',
  },
  {
    title: 'Distance turns apparent into absolute',
    body: 'The distance modulus (m − M = 5 log₁₀ d/10 pc) converts apparent V into absolute magnitude Mv. For M34 at ~470 pc, every cluster member shares that offset, so stars at the same Mv have similar intrinsic luminosity regardless of where they fall in the survey field.',
  },
  {
    title: 'The main sequence is a mass sequence',
    body: 'Most cluster members sit on the main sequence — hydrogen fusing in the core. High-mass stars are bluer and brighter (lower Mv); low-mass stars trail down the red side. The band is not a single line but a sequence whose width comes from age spread, binaries, rotation, and measurement noise.',
  },
  {
    title: 'Isochrones: curves of constant age',
    body: 'An isochrone is a model prediction of where single stars of all masses should fall if they formed together. Stellar-evolution codes (Yonsei–Yale in Project Midas) integrate structure and nuclear burning to draw these curves for a chosen age and metallicity.',
  },
  {
    title: 'Age shifts the whole diagram',
    body: 'Younger isochrones sit higher and bluer: massive stars have not yet evolved off the main sequence. As a cluster ages, the turnoff — where the band bends toward giants — moves down the sequence. Compare 100, 200, 400, and 600 Myr tracks below; each predicts a different turnoff by nearly a magnitude.',
  },
  {
    title: 'M34 at ~200 million years',
    body: 'Photometry, rotation studies (WOCS), and gyrochronology converge on an age near 180–220 Myr for M34. The 200 Myr Yonsei–Yale isochrone matches the observed main-sequence locus; the turnoff near Mv ≈ 1 and B−V ≈ 0.3 corresponds to ~2 M☉ stars leaving core hydrogen burning. Ages of 100 or 400 Myr leave systematic residuals at the turnoff.',
  },
  {
    title: 'Binaries shift the band',
    body: 'An unresolved equal-mass pair adds light without changing color much — the system appears ~0.75 mag brighter than a single star at the same B−V. Project Midas measures how far each star sits between the single-star isochrone and a parallel binary track (the Q-value) to flag unresolved companions.',
  },
];

const HR_DIAGRAM_MODES: HRDiagramMode[] = [
  'stars',
  'stars',
  'main-sequence',
  'isochrone-intro',
  'age-compare',
  'age-fit',
  'binary',
];

const HR_CAPTIONS = [
  'Sample of Midas BVR photometry. Hover a point for magnitudes. Axes: observational HR diagram (B−V vs Mv).',
  'Same stars after applying the cluster distance modulus (~470 pc). Faint field stars would not cluster here.',
  'The diagonal main sequence: mass increases toward the upper left. Orange curve: Yonsei–Yale 0.2 Gyr single-star model.',
  'Isochrones summarize stellar-evolution theory — one curve per age at fixed chemistry (here solar Z, [Fe/H] = 0).',
  'Four ages from the legacy ISO table: 100 · 200 · 400 · 600 Myr. Dashed cyan: PARSEC v1.2S at the same ages.',
  'Best-fit age for M34: ~200 Myr (gold YY track). Dashed cyan PARSEC turnoff is fainter — model choice affects binary cuts.',
  'Gold: single-star isochrone. Dashed blue: equal-mass binary track (Mv offset −0.75). Gold points: Excel binary candidates (171); hover for singles/binaries flags from the Control sheet.',
];

interface HomePageProps {
  scrollTo?: string;
}

export default function HomePage({ scrollTo }: HomePageProps) {
  const { activeIndex, containerRef } = useScrolly(HR_STEPS.length);
  const [hrDered, setHrDered] = useState(false);
  const [hrMembersOnly, setHrMembersOnly] = useState(false);

  const hrStars = useMemo(() => {
    let stars = data.stars;
    if (hrMembersOnly) {
      stars = stars.filter((s) => s.cgMember);
    }
    if (hrDered) {
      stars = stars.map((s) => ({
        ...s,
        bv: s.bv0 ?? s.bv,
        mv: s.mv0 ?? s.mv,
      }));
    }
    return stars;
  }, [hrDered, hrMembersOnly]);

  useEffect(() => {
    if (!scrollTo) return;
    const el = document.getElementById(scrollTo);
    if (el) {
      requestAnimationFrame(() => el.scrollIntoView({ behavior: 'smooth', block: 'start' }));
    }
  }, [scrollTo]);

  const hrHighlight: Array<'all' | 'single' | 'binary'> = [
    'all',
    'all',
    'all',
    'all',
    'all',
    'all',
    'binary',
  ];

  return (
    <>
      <Header />

      <section className="hero hero--with-image">
        <div className="hero__backdrop" aria-hidden="true">
          <img
            src={`${import.meta.env.BASE_URL}images/m34-hero.jpg`}
            alt=""
            className="hero__photo"
            loading="eager"
            fetchPriority="high"
          />
          <div className="hero__scrim" />
        </div>
        <div className="hero__content">
          <p className="hero__kicker">NGC 1039 · M34 · proving ground for Credence</p>
          <h1 className="hero__title">The spiral cluster, revisited</h1>
          <p className="hero__deck">
            We revived legacy Midas photometry for M34 — binary stars in a ~200 Myr open cluster,
            reconnected to Gaia and modern surveys. That work became the prototype for{' '}
            <a href="/credence" className="hero__link">Credence</a>: ingest heterogeneous catalogs,
            resolve each star to one record, infer membership and binarity, and display it all in a
            planetarium-scale sky atlas.
          </p>
          <div className="hero__meta">
            <span>~470 pc · ~200 Myr</span>
            <span>{data.meta.n_sample.toLocaleString()} stars in this sample</span>
            <a href="/credence" className="hero__meta-link">
              Where it&apos;s going → Credence
            </a>
          </div>
        </div>
      </section>

      <section id="history" className="section section--rule">
        <p className="section__label">Chapter 1</p>
        <h2 className="section__title">Two centuries of looking at the same stars</h2>
        <div className="section__prose">
          <p className="lead">
            M34 is one of the nearest open clusters — visible in binoculars, yet still rich enough to
            test how stars form, spin, pair up, and fade.
          </p>
          <p>
            Each era added a layer: visual discovery, photographic astrometry, CCD photometry,
            radial velocities, space-based parallaxes, and infrared-sensitive binary censuses. Project
            Midas sits in the photometric layer, now being reconnected to everything that came after.
          </p>
        </div>
        <div style={{ marginTop: '2.5rem' }}>
          <HistoryTimeline events={data.history} />
        </div>
      </section>

      <section id="sky" className="section section--rule">
        <p className="section__label">Chapter 2</p>
        <h2 className="section__title">What M34 looks like through a telescope</h2>
        <div className="section__prose">
          <p className="lead">
            M34 is bright enough to see in binoculars under dark skies — a loose spray of stars in Perseus.
            Professional archives preserve how that same patch looked on photographic plates, modern CCDs, and
            infrared surveys.
          </p>
        </div>

        <div style={{ marginTop: '2.5rem' }}>
          <h3
            style={{
              fontFamily: 'var(--sans)',
              fontSize: '1.1rem',
              margin: '0 0 1rem',
              fontWeight: 600,
            }}
          >
            In the constellation map
          </h3>
          <ConstellationFinder />
        </div>

        <div style={{ marginTop: '3rem' }}>
          <h3
            style={{
              fontFamily: 'var(--sans)',
              fontSize: '1.1rem',
              margin: '0 0 1rem',
              fontWeight: 600,
            }}
          >
            Through the telescope archive
          </h3>
          <SkyImagery />
        </div>
      </section>

      <section id="science" className="section section--rule">
        <p className="section__label">Chapter 3</p>
        <h2 className="section__title">Reading the Hertzsprung–Russell diagram</h2>
        <div className="section__prose">
          <p className="lead">
            The HR diagram is the central tool for open-cluster work: it turns magnitudes and colors
            into a picture of mass, age, and evolution — and reveals stars that do not fit the
            single-star story.
          </p>
          <p>
            Scroll the steps at left to walk from raw photometry through isochrone fitting to the
            binary diagnostics that define Project Midas.
          </p>
        </div>

        <div style={{ marginTop: '2rem' }}>
          <HRExplainer />
        </div>

        <div className="section__prose" style={{ marginTop: '2rem' }}>
          <p>
            The isochrone gallery compares Yonsei–Yale ages side by side — the same tracks rebuilt
            from legacy ISO.csv. Toggle dashed cyan PARSEC v1.2S curves to see how model choice shifts
            the turnoff. Use the filters below the gallery for uniform de-reddening (E(B−V) ={' '}
            {data.meta.ebv ?? 0.07}) and Cantat-Gaudin membership (P ≥ {data.meta.cg_member_threshold ?? 0.7}).
          </p>
        </div>

        <div style={{ marginTop: '2.5rem' }}>
          <IsochroneExplorer stars={hrStars} />
        </div>

        <div className="hr-filters" role="group" aria-label="HR diagram filters">
          <label className="hr-filters__item">
            <input
              type="checkbox"
              checked={hrDered}
              onChange={(e) => setHrDered(e.target.checked)}
            />
            De-reddened (E(B−V) = {data.meta.ebv ?? 0.07})
          </label>
          <label className="hr-filters__item">
            <input
              type="checkbox"
              checked={hrMembersOnly}
              onChange={(e) => setHrMembersOnly(e.target.checked)}
            />
            Cantat-Gaudin members only (P ≥ {data.meta.cg_member_threshold ?? 0.7})
          </label>
        </div>

        <div className="scrolly" ref={containerRef} style={{ marginTop: '1.25rem' }}>
          <div className="scrolly__steps">
            {HR_STEPS.map((step, i) => (
              <article
                key={step.title}
                data-scrolly-step={i}
                className={`scrolly__step${activeIndex === i ? ' is-active' : ''}`}
              >
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </article>
            ))}
          </div>
          <div className="scrolly__graphic">
            <HRDiagram
              stars={hrStars}
              isochrone={data.isochrone}
              ageIsochrones={ISOCHRONE_AGES}
              compareAges={SCROLLY_COMPARE_AGES}
              mode={HR_DIAGRAM_MODES[activeIndex] ?? 'stars'}
              highlight={hrHighlight[activeIndex] ?? 'all'}
            />
            <div className="scrolly__caption">{HR_CAPTIONS[activeIndex] ?? HR_CAPTIONS[0]}</div>
          </div>
        </div>
      </section>

      <section id="data" className="section section--rule">
        <p className="section__label">Chapter 4</p>
        <h2 className="section__title">Many catalogs, one patch of sky</h2>
        <div className="section__prose">
          <p className="lead">
            M34 is not understudied — it is <em>overlapped</em>. Legacy Midas photometry, Jones &amp;
            Prosser proper-motion members, and Gaia DR3 all cover the same ~35′ field. Toggle layers
            below to compare footprints and density.
          </p>
          <p>
            Gaia DR3 provides the background field ({catalogBundle.layers.find((l) => l.id === 'gaia_field')?.totalCount.toLocaleString() ?? '15,211'} sources in a 0.5° cone from{' '}
            <code>gaia_cone.py</code>). Cantat-Gaudin membership, Malofeeva IR binaries,
            and WOCS rotation/RV targets are toggleable layers with join-table flags on Midas hover.
          </p>
          <p>
            Malofeeva et al. (2023) and Cantat-Gaudin &amp; Anders (2020) come from VizieR; WOCS maps
            the 120 Meibom et al. (2011) rotation/R V targets (parent survey: 5,656 V-band light curves).
          </p>
        </div>
        <div style={{ marginTop: '2rem' }}>
          <DataExplorer bundle={catalogBundle} />
        </div>
      </section>

      <section id="compare" className="section section--rule">
        <p className="section__label">Chapter 5</p>
        <h2 className="section__title">Joining the layers</h2>
        <div className="section__prose">
          <p className="lead">
            Legacy Midas photometry, Jones &amp; Prosser proper-motion members, and Gaia DR3 all
            cover the same ~35′ field. The revival work joined those layers into one table — see{' '}
            <a href="/continued">Midas Continued</a> for the full pipeline and findings.
          </p>
          <p>
            Toggle layers below to compare footprints and density. Excel binary candidates appear in
            gold on the final HR scrolly step in <a href="/science">Chapter 3</a>.
          </p>
        </div>
        <DataComparison />
        <MethodComparison />
      </section>

      <section id="code" className="section section--rule">
        <p className="section__label">Chapter 6</p>
        <h2 className="section__title">Try the arithmetic yourself</h2>
        <div className="section__prose">
          <p className="lead">
            Stellar data science often reduces to careful unit conversions and comparisons to models.
            Each example below runs entirely in your browser via Pyodide — the same arithmetic
            underpins the scripts in <code>research/scripts/</code>.
          </p>
          <p>
            Read the <strong>Inputs</strong> and <strong>Outputs</strong> panels before running.
            Edit the Python in your local checkout to try your own star measurements.
          </p>
        </div>
        <CodeDemoGallery demos={CODE_DEMOS} />
      </section>

      <section id="credence" className="section section--rule">
        <p className="section__label">What&apos;s next</p>
        <h2 className="section__title">From M34 to the whole sky</h2>
        <div className="section__prose">
          <p className="lead">
            The Midas revival taught us how to ingest legacy photometry, resolve it against modern
            catalogs, and infer properties like membership and binarity. That pipeline — and the
            gaps we found comparing B−V track offsets to Gaia+WISE IR diagnostics — became the
            seed for Credence.
          </p>
          <p>
            Credence is a planetarium-scale atlas: ingest heterogeneous star catalogs, resolve
            duplicates across surveys, infer membership and binary likelihood with calibrated models,
            and display the results in an explorable sky view. M34 was the proving ground; Credence
            extends the same architecture to open clusters across the Galaxy.
          </p>
          <p>
            Read the full Credence design — pipeline tiers, infer benchmarks (F1 ≈ 0.66 vs legacy Q
            ≈ 0.55 on M34), and the roadmap from prototype to galaxy-scale release — on the{' '}
            <a href="/credence">Credence page</a>. Phase writeups, findings, and the toolchain live
            on <a href="/continued">Midas Continued</a>.
          </p>
        </div>
      </section>

      <Footer />
    </>
  );
}
