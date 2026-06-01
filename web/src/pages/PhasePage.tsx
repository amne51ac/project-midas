import { useEffect } from 'react';
import { Footer } from '../components/Footer';
import { Header } from '../components/Header';
import { PhaseWriteup } from '../components/PhaseWriteup';
import { PHASE_STATUS_CLASS, PhaseDetailTracker, StatusLegend } from '../components/roadmapShared';
import {
  getPhaseById,
  PHASE_STATUS_LABELS,
  ROADMAP_PHASES,
  type PhaseExploration,
} from '../data/roadmap';
import { homeSectionHref, phasePageHref, type PhaseSectionId } from '../hooks/useHashRoute';

interface Props {
  phaseId: string;
  scrollTo?: PhaseSectionId;
}

export function PhasePage({ phaseId, scrollTo }: Props) {
  const phase = getPhaseById(phaseId);

  useEffect(() => {
    if (!scrollTo) return;
    const el = document.getElementById(`phase-${scrollTo}`);
    if (el) {
      requestAnimationFrame(() => el.scrollIntoView({ behavior: 'smooth', block: 'start' }));
    }
  }, [scrollTo, phaseId]);

  if (!phase) {
    return (
      <>
        <Header />
        <section className="section phase-page">
          <p className="section__label">Roadmap</p>
          <h1 className="section__title">Phase not found</h1>
          <p className="section__prose">
            <a href={homeSectionHref('roadmap')}>← Back to roadmap</a>
          </p>
        </section>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Header />
      <section className="section phase-page">
        <nav className="phase-page__breadcrumb" aria-label="Breadcrumb">
          <a href={homeSectionHref('roadmap')}>Roadmap</a>
          <span aria-hidden="true"> / </span>
          <span>{phase.label}</span>
        </nav>

        <header id="phase-overview" className={`phase-page__header ${PHASE_STATUS_CLASS[phase.status]}`}>
          <div>
            <p className="section__label">{phase.label}</p>
            <h1 className="phase-page__title">{phase.title}</h1>
          </div>
          <div className="phase-page__badges">
            <span className={`roadmap-phase__badge roadmap-phase__badge--${phase.status}`}>
              {PHASE_STATUS_LABELS[phase.status]}
            </span>
          </div>
        </header>

        <div className="section__prose phase-page__intro">
          <p className="lead">{phase.summary}</p>
        </div>

        <div id="phase-writeup">
          <PhaseWriteup phaseId={phase.id} />
        </div>

        <h2 id="phase-tracker" className="section__subhead">Task tracker</h2>
        <StatusLegend />
        <PhaseDetailTracker phase={phase} />

        <h2 id="phase-explorations" className="section__subhead">Explorations</h2>
        <p className="section__prose phase-page__explore-intro">
          Phase-specific entry points — interactive sections on the main site and pipeline milestones.
        </p>
        <div className="phase-explorations">
          {phase.explorations.map((item: PhaseExploration) => (
            <article key={item.id} className="phase-exploration-card">
              {item.stat && <p className="phase-exploration-card__stat">{item.stat}</p>}
              <h3 className="phase-exploration-card__title">{item.title}</h3>
              <p className="phase-exploration-card__summary">{item.summary}</p>
              {item.homeHref ? (
                <a href={item.homeHref} className="phase-exploration-card__link">
                  Open on main site →
                </a>
              ) : (
                <span className="phase-exploration-card__link phase-exploration-card__link--muted">
                  Coming in this phase
                </span>
              )}
            </article>
          ))}
        </div>

        <nav className="phase-page__siblings" aria-label="Other phases">
          {ROADMAP_PHASES.filter((p) => p.id !== phase.id).map((p) => (
            <a key={p.id} href={phasePageHref(p.id)} className="phase-page__sibling">
              {p.label}: {p.title}
            </a>
          ))}
        </nav>

        <p className="phase-page__back">
          <a href={homeSectionHref('roadmap')}>← Back to overall roadmap</a>
        </p>
      </section>
      <Footer />
    </>
  );
}
