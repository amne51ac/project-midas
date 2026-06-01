import {
  phaseProgress,
  WORK_STATUS_LABELS,
  type PhaseStatus,
  type RoadmapPhase,
  type RoadmapTask,
  type WorkStatus,
} from '../data/roadmap';

export const WORK_STATUS_CLASS: Record<WorkStatus, string> = {
  done: 'roadmap-task__status--done',
  in_progress: 'roadmap-task__status--in-progress',
  planned: 'roadmap-task__status--planned',
};

export const PHASE_STATUS_CLASS: Record<PhaseStatus, string> = {
  complete: 'roadmap-phase--complete',
  active: 'roadmap-phase--active',
  upcoming: 'roadmap-phase--upcoming',
};

export const PHASE_NODE_CLASS: Record<PhaseStatus, string> = {
  complete: 'roadmap-track__node--complete',
  active: 'roadmap-track__node--active',
  upcoming: 'roadmap-track__node--upcoming',
};

export function StatusLegend() {
  const items: WorkStatus[] = ['done', 'in_progress', 'planned'];
  return (
    <div className="roadmap-legend" aria-label="Work status legend">
      {items.map((status) => (
        <span key={status} className={`roadmap-legend__item ${WORK_STATUS_CLASS[status]}`}>
          {WORK_STATUS_LABELS[status]}
        </span>
      ))}
    </div>
  );
}

export function PhaseTrack({ phases }: { phases: RoadmapPhase[] }) {
  return (
    <div className="roadmap-track" aria-hidden="true">
      {phases.map((phase, index) => (
        <div key={phase.id} className="roadmap-track__segment">
          <div className={`roadmap-track__node ${PHASE_NODE_CLASS[phase.status]}`}>
            <span className="roadmap-track__node-label">{phase.label.replace('Phase ', '')}</span>
          </div>
          {index < phases.length - 1 && <div className="roadmap-track__connector" />}
        </div>
      ))}
    </div>
  );
}

export function TaskRow({ task }: { task: RoadmapTask }) {
  return (
    <li className={`roadmap-task roadmap-task--${task.status}`}>
      <span className={`roadmap-task__status ${WORK_STATUS_CLASS[task.status]}`}>
        {WORK_STATUS_LABELS[task.status]}
      </span>
      <div className="roadmap-task__body">
        <p className="roadmap-task__title">{task.title}</p>
        {task.detail && <p className="roadmap-task__detail">{task.detail}</p>}
      </div>
    </li>
  );
}

export function PhaseDetailTracker({ phase }: { phase: RoadmapPhase }) {
  const progress = phaseProgress(phase);
  const doneCount = phase.tasks.filter((t) => t.status === 'done').length;

  return (
    <article className={`roadmap-phase roadmap-phase--detail ${PHASE_STATUS_CLASS[phase.status]}`}>
      <div className="roadmap-phase__progress-wrap">
        <div className="roadmap-phase__progress-meta">
          <span>
            {doneCount} / {phase.tasks.length} tasks complete
          </span>
          <span>{progress}%</span>
        </div>
        <div
          className="roadmap-phase__progress"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${phase.label} progress`}
        >
          <span className="roadmap-phase__progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <ul className="roadmap-tasks">
        {phase.tasks.map((task) => (
          <TaskRow key={task.id} task={task} />
        ))}
      </ul>
    </article>
  );
}
