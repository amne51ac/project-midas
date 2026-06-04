import { useEffect } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { RoadmapOverview } from '../components/RoadmapOverview';
import { ToolsInventory } from '../components/ToolsInventory';
import { DataRelease } from '../components/DataRelease';
import { PhaseSection } from '../components/PhaseSection';
import { FINDINGS } from '../data/findings';
import { ROADMAP_PHASES } from '../data/roadmap';
import type { ContinuedSectionId } from '../routing/appRoute';

interface Props {
  scrollTo?: ContinuedSectionId;
}

export function ContinuedPage({ scrollTo }: Props) {
  const { headline, lede, atAGlance, sections, limitations, openQuestions } = FINDINGS;

  useEffect(() => {
    if (!scrollTo) return;
    const el = document.getElementById(scrollTo);
    if (el) {
      requestAnimationFrame(() => el.scrollIntoView({ behavior: 'smooth', block: 'start' }));
    }
  }, [scrollTo]);

  return (
    <>
      <Header />
      <main className="findings-page continued-page">
        <div id="overview" className="findings-page__hero section">
          <p className="section__label">Revival work</p>
          <h1 className="findings-page__title">Midas Continued</h1>
          <p className="findings-page__lede lead">
            Four phases took legacy B−V photometry for M34, reconnected it to Gaia-era catalogs,
            validated the original binary heuristic, and synthesized what the pipeline actually
            tells us. This page collects the roadmap, phase writeups, findings, and toolchain in one place.
          </p>
        </div>

        <section className="section section--rule" aria-label="Project roadmap">
          <h2 className="section__subhead">Project roadmap</h2>
          <div className="section__prose">
            <p>
              Reviving Project Midas is a phased integration problem: preserve legacy photometry,
              wire in Gaia-era catalogs, validate the Q-value heuristic against modern binary
              diagnostics, then synthesize results into a methods-focused write-up.
            </p>
          </div>
          <RoadmapOverview />
        </section>

        {ROADMAP_PHASES.map((phase) => (
          <PhaseSection key={phase.id} phaseId={phase.id} />
        ))}

        <section id="findings" className="section section--rule" aria-label="Synthesis">
          <p className="section__label">Synthesis</p>
          <h2 className="findings-page__title">{headline}</h2>
          <p className="findings-page__lede lead">{lede}</p>
        </section>

        <section className="findings-page__glance section section--rule" aria-label="Key numbers">
          <h3 className="section__subhead">At a glance</h3>
          <dl className="findings-glance">
            {atAGlance.map(({ label, value, detail }) => (
              <div key={label} className="findings-glance__item">
                <dt>{label}</dt>
                <dd>
                  <span className="findings-glance__value">{value}</span>
                  {detail && <span className="findings-glance__detail">{detail}</span>}
                </dd>
              </div>
            ))}
          </dl>
        </section>

        {sections.map((block) => (
          <section
            key={block.id}
            id={block.id}
            className="findings-section section section--rule"
          >
            <p className="findings-section__phase">{block.phase}</p>
            <h3 className="findings-section__title">{block.title}</h3>
            {block.paragraphs.map((p) => (
              <p key={p.slice(0, 40)} className="section__prose">
                {p}
              </p>
            ))}
            {block.stats && block.stats.length > 0 && (
              <dl className="findings-section__stats">
                {block.stats.map(({ label, value, detail }) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>
                      {value}
                      {detail && <span className="findings-glance__detail"> — {detail}</span>}
                    </dd>
                  </div>
                ))}
              </dl>
            )}
            {block.bullets && (
              <ul className="findings-section__list section__prose">
                {block.bullets.map((b) => (
                  <li key={b.slice(0, 30)}>{b}</li>
                ))}
              </ul>
            )}
            {block.href && (
              <p className="findings-section__link">
                <a href={block.href}>{block.hrefLabel ?? 'Read more'}</a>
              </p>
            )}
          </section>
        ))}

        <section id="tools" className="section section--rule">
          <h2 className="section__subhead">Toolchain inventory</h2>
          <ToolsInventory />
          <DataRelease />
        </section>

        <section id="questions" className="findings-page__closing section section--rule">
          <h2 className="section__subhead">Limitations</h2>
          <ul className="findings-section__list section__prose">
            {limitations.map((item) => (
              <li key={item.slice(0, 30)}>{item}</li>
            ))}
          </ul>

          <h2 className="section__subhead">Open questions</h2>
          <ul className="findings-section__list section__prose">
            {openQuestions.map((item) => (
              <li key={item.slice(0, 30)}>{item}</li>
            ))}
          </ul>
        </section>
      </main>
      <Footer />
    </>
  );
}

export default ContinuedPage;
