import { ConstellationFinder } from './components/ConstellationFinder';
import { SkyImagery } from './components/SkyImagery';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { HRExplainer } from './components/HRExplainer';
import { HRDiagram, type HRDiagramMode } from './components/HRDiagram';
import { HistoryTimeline } from './components/HistoryTimeline';
import { DataExplorer } from './components/DataExplorer';
import catalogs from './data/m34_catalogs.json';
import type { CatalogBundle } from './data/catalogTypes';
import { PhaseTimeline, ToolsMatrix } from './components/PhaseTimeline';
import { CodeRunner } from './components/CodeRunner';
import { useScrolly } from './hooks/useScrolly';
import dataset from './data/m34_sample.json';
import { ISOCHRONE_AGES, SCROLLY_COMPARE_AGES } from './data/isochrones';
import { IsochroneExplorer } from './components/IsochroneExplorer';
import type { DatasetMeta } from './data/types';

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
  'Four ages from the legacy ISO table: 100 · 200 · 400 · 600 Myr. Younger clusters sit higher; circles mark turnoffs.',
  'Best-fit age for M34: ~200 Myr (gold). Turnoff near Mv ≈ 1, B−V ≈ 0.3 (~2 M☉). Other ages leave residuals at the bend.',
  'Gold: single-star isochrone. Dashed blue: equal-mass binary track (Mv offset −0.75). Stars between the lines are Midas binary candidates.',
];

const DISTANCE_PC = 470;

const DEMO_ABS_MAG = `# Distance modulus: m - M = 5 log10(d/10 pc)
import math
d_pc = ${DISTANCE_PC}
V_app = 10.5
M_abs = V_app - 5 * math.log10(d_pc / 10)
print(f"Apparent V = {V_app}")
print(f"Distance   = {d_pc} pc")
print(f"Absolute M_V = {M_abs:.2f}")
print()
print("For M34, every member at ~470 pc shares this conversion.")
`;

const DEMO_BV_Q = `# B-V color and deviation from a simple isochrone line
B, V = 10.8, 10.2
bv = B - V
# Expected B-V at this Mv (illustrative linear MS)
Mv = V - 5 * __import__('math').log10(470/10)
xbv = 0.95 - 0.05 * (Mv - 5)  # rough toy relation
bvdev = bv - xbv
print(f"B-V observed  = {bv:.3f}")
print(f"B-V expected  = {xbv:.3f}")
print(f"Deviation     = {bvdev:+.3f} mag")
print()
if abs(bvdev) < 0.05:
    print("→ Consistent with single main-sequence star")
else:
    print("→ Candidate binary or non-member")
`;

export default function App() {
  const { activeIndex, containerRef } = useScrolly(HR_STEPS.length);
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

      <section className="hero">
        <p className="hero__kicker">NGC 1039 · Messier 34 · Perseus</p>
        <h1 className="hero__title">The spiral cluster, revisited</h1>
        <p className="hero__deck">
          An interactive history of M34 — from Messier&apos;s discovery to Gaia — and Project Midas:
          photometric search for unresolved binaries in a 200-million-year-old open cluster.
        </p>
        <div className="hero__meta">
          <span>~470 pc · ~200 Myr</span>
          <span>{data.meta.n_sample.toLocaleString()} stars shown (sample)</span>
          <span>Scroll to explore</span>
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

        <div style={{ marginTop: '2.5rem' }}>
          <IsochroneExplorer stars={data.stars} />
        </div>

        <div className="scrolly" ref={containerRef} style={{ marginTop: '2.5rem' }}>
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
              stars={data.stars}
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
            Gaia cluster candidates use a parallax cut (1.5–3.2 mas) as a stand-in until Cantat-Gaudin
            membership probabilities are ingested. Malofeeva IR binaries and WOCS light curves are listed
            for reference — cross-match is on the research roadmap.
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
          <p>
            Project Midas aims to cross-match every legacy star to Gaia DR3 source IDs, replace
            Jones–Prosser flags with Cantat-Gaudin probabilities, and validate Q-value binary candidates
            against Malofeeva IR diagrams and WOCS radial velocities — without double-counting the same
            physical system.
          </p>
          <p>
            The interactive map in <a href="#data">Chapter 4</a> shows what is already loaded locally;
            published catalogs awaiting ingest appear in the sidebar with reference counts.
          </p>
        </div>
      </section>

      <section id="code" className="section section--rule">
        <p className="section__label">Chapter 6</p>
        <h2 className="section__title">Try the arithmetic yourself</h2>
        <div className="section__prose">
          <p>
            Stellar data science often reduces to careful unit conversions and comparisons to models.
            These snippets run entirely in your browser — the same logic underpins the research scripts
            in <code>research/scripts/</code>.
          </p>
        </div>
        <CodeRunner title="Absolute magnitude from distance" code={DEMO_ABS_MAG} />
        <CodeRunner title="B−V deviation (toy isochrone)" code={DEMO_BV_Q} />
      </section>

      <section id="roadmap" className="section section--rule">
        <p className="section__label">Chapter 7</p>
        <h2 className="section__title">Questions we are aiming to answer</h2>
        <div className="section__prose">
          <ul>
            <li>How complete is B−V isochrone binary detection compared to Gaia+IR methods?</li>
            <li>Which Midas Q-value candidates confirm in Malofeeva, WOCS RV, or Gaia astrometry?</li>
            <li>What binary fraction vs. mass emerges when catalogs are joined without double-counting?</li>
            <li>Do legacy Midas photometry stars add value beyond Gaia G/BP/RP at faint magnitudes?</li>
            <li>Can white dwarf candidates from Rubin et al. be confirmed with DR4 astrometry?</li>
          </ul>
        </div>

        <h3
          style={{
            fontFamily: 'var(--sans)',
            fontSize: '1.1rem',
            marginTop: '2.5rem',
            marginBottom: 0,
          }}
        >
          Project phases
        </h3>
        <PhaseTimeline />

        <h3
          style={{
            fontFamily: 'var(--sans)',
            fontSize: '1.1rem',
            marginTop: '2.5rem',
            marginBottom: 0,
          }}
        >
          Tools: existing vs. to build
        </h3>
        <ToolsMatrix />

        <div className="section__prose" style={{ marginTop: '2.5rem' }}>
          <p>
            <strong>Repository layout:</strong> <code>web/</code> — this site ·{' '}
            <code>research/</code> — data, scripts, notebooks · Legacy Midas code lives in the
            sibling archive and will be linked as provenance.
          </p>
          <p>
            <strong>Hosting:</strong> Static build deploys to GitHub Pages and GitLab Pages from CI.
            Set <code>VITE_BASE_PATH</code> to your repo path (e.g. <code>/project-midas/</code>) or{' '}
            <code>/</code> for a custom domain.
          </p>
        </div>
      </section>

      <Footer />
    </>
  );
}
