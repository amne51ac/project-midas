import {
  countTasksByStatus,
  overallProgress,
  PHASE_STATUS_LABELS,
  phaseProgress,
  ROADMAP_PHASES,
} from '../data/roadmap';
import { phasePageHref } from '../routing/appRoute';
import { PHASE_STATUS_CLASS, PhaseTrack } from './roadmapShared';

function RoadmapSummary() {
  const progress = overallProgress(ROADMAP_PHASES);
  const counts = countTasksByStatus(ROADMAP_PHASES);
  const total = counts.done + counts.in_progress + counts.planned;

  return (
    <div className="roadmap-summary">
      <div className="roadmap-summary__head">
        <div>
          <p className="roadmap-summary__label">Overall progress</p>
          <p className="roadmap-summary__value">{progress}%</p>
        </div>
        <dl className="roadmap-summary__stats">
          <div>
            <dt>{counts.done}</dt>
            <dd>Complete</dd>
          </div>
          <div>
            <dt>{counts.in_progress}</dt>
            <dd>In progress</dd>
          </div>
          <div>
            <dt>{counts.planned}</dt>
            <dd>Planned</dd>
          </div>
          <div>
            <dt>{total}</dt>
            <dd>Total tasks</dd>
          </div>
        </dl>
      </div>
      <div
        className="roadmap-summary__bar"
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Overall project progress"
      >
        <span className="roadmap-summary__bar-fill" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}

function PhaseOverviewCard({ phase }: { phase: (typeof ROADMAP_PHASES)[number] }) {
  const progress = phaseProgress(phase);

  return (
    <a href={phasePageHref(phase.id)} className={`phase-overview-card ${PHASE_STATUS_CLASS[phase.status]}`}>
      <div className="phase-overview-card__head">
        <p className="phase-overview-card__label">{phase.label}</p>
        <span className={`roadmap-phase__badge roadmap-phase__badge--${phase.status}`}>
          {PHASE_STATUS_LABELS[phase.status]}
        </span>
      </div>
      <h4 className="phase-overview-card__title">{phase.title}</h4>
      <p className="phase-overview-card__summary">{phase.summary}</p>
      <div className="phase-overview-card__meta">
        <span>{progress}% complete</span>
      </div>
      <span className="phase-overview-card__cta">Open phase →</span>
    </a>
  );
}

export function RoadmapOverview() {
  return (
    <div className="project-roadmap project-roadmap--overview">
      <RoadmapSummary />
      <PhaseTrack phases={ROADMAP_PHASES} />
      <div className="phase-overview-grid">
        {ROADMAP_PHASES.map((phase) => (
          <PhaseOverviewCard key={phase.id} phase={phase} />
        ))}
      </div>
    </div>
  );
}
