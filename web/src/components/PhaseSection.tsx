import { PhaseWriteup } from './PhaseWriteup';
import { PHASE_STATUS_CLASS, PhaseDetailTracker, StatusLegend } from './roadmapShared';
import {
  getPhaseById,
  PHASE_STATUS_LABELS,
  type PhaseExploration,
} from '../data/roadmap';

interface Props {
  phaseId: string;
}

export function PhaseSection({ phaseId }: Props) {
  const phase = getPhaseById(phaseId);
  if (!phase) return null;

  return (
    <section id={phase.id} className="section section--rule phase-page continued-phase">
      <header className={`phase-page__header ${PHASE_STATUS_CLASS[phase.status]}`}>
        <div>
          <p className="section__label">{phase.label}</p>
          <h2 className="phase-page__title">{phase.title}</h2>
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

      <PhaseWriteup phaseId={phase.id} />

      <h3 className="section__subhead">Task tracker</h3>
      <StatusLegend />
      <PhaseDetailTracker phase={phase} />

      <h3 className="section__subhead">Explorations</h3>
      <p className="section__prose phase-page__explore-intro">
        Phase-specific entry points — interactive sections on the main site and pipeline milestones.
      </p>
      <div className="phase-explorations">
        {phase.explorations.map((item: PhaseExploration) => (
          <article key={item.id} className="phase-exploration-card">
            {item.stat && <p className="phase-exploration-card__stat">{item.stat}</p>}
            <h4 className="phase-exploration-card__title">{item.title}</h4>
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
    </section>
  );
}

export function PhaseNotFound({ phaseId }: { phaseId: string }) {
  return (
    <section className="section phase-page">
      <p className="section__label">Continued</p>
      <h1 className="section__title">Section not found</h1>
      <p className="section__prose">
        No phase named &ldquo;{phaseId}&rdquo;.{' '}
        <a href="/continued">← Back to Midas Continued</a>
      </p>
    </section>
  );
}
