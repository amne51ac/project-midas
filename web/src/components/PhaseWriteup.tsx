import {
  getPhaseWriteup,
  type PhaseExample,
  type PhaseStep,
} from '../data/phaseWriteups';
import { formatCompletedDate } from '../data/roadmap';

function ExampleBlock({ example }: { example: PhaseExample }) {
  const className = `phase-step__example phase-step__example--${example.kind}`;

  if (example.kind === 'stats') {
    return (
      <div className={className}>
        {example.label && <p className="phase-step__example-label">{example.label}</p>}
        <p className="phase-step__stat">{example.body}</p>
      </div>
    );
  }

  if (example.kind === 'command' || example.kind === 'code') {
    return (
      <div className={className}>
        {example.label && <p className="phase-step__example-label">{example.label}</p>}
        <pre className="phase-step__code">
          <code>{example.body}</code>
        </pre>
      </div>
    );
  }

  return (
    <div className={className}>
      {example.label && <p className="phase-step__example-label">{example.label}</p>}
      <p className="phase-step__note">{example.body}</p>
    </div>
  );
}

function StepArticle({ step, index }: { step: PhaseStep; index: number }) {
  return (
    <article className="phase-step" id={`step-${step.id}`}>
      <header className="phase-step__header">
        <span className="phase-step__number">{String(index + 1).padStart(2, '0')}</span>
        <div>
          <h3 className="phase-step__title">{step.title}</h3>
          {step.completedDate && (
            <p className="phase-step__date">
              Completed {formatCompletedDate(step.completedDate)}
            </p>
          )}
        </div>
      </header>

      <div className="phase-step__body section__prose">
        {step.paragraphs.map((p) => (
          <p key={p.slice(0, 40)}>{p}</p>
        ))}
      </div>

      {step.examples && step.examples.length > 0 && (
        <div className="phase-step__examples">
          {step.examples.map((ex) => (
            <ExampleBlock key={`${ex.kind}-${ex.label ?? ex.body.slice(0, 24)}`} example={ex} />
          ))}
        </div>
      )}

      {step.homeHref && (
        <p className="phase-step__link">
          <a href={step.homeHref}>{step.homeLabel ?? 'See on main site'} →</a>
        </p>
      )}
    </article>
  );
}

interface Props {
  phaseId: string;
}

export function PhaseWriteup({ phaseId }: Props) {
  const writeup = getPhaseWriteup(phaseId);
  if (!writeup) return null;

  return (
    <section className="phase-writeup" aria-labelledby="phase-writeup-heading">
      <h2 id="phase-writeup-heading" className="section__subhead">
        What we did
      </h2>

      <div className="section__prose phase-writeup__overview">
        {writeup.overview.map((p) => (
          <p key={p.slice(0, 48)}>{p}</p>
        ))}
      </div>

      <ol className="phase-steps">
        {writeup.steps.map((step, i) => (
          <li key={step.id}>
            <StepArticle step={step} index={i} />
          </li>
        ))}
      </ol>

      {writeup.outcomes && writeup.outcomes.length > 0 && (
        <aside className="phase-outcomes" aria-label="Phase outcomes">
          <h3 className="phase-outcomes__title">At a glance</h3>
          <dl className="phase-outcomes__grid">
            {writeup.outcomes.map(({ label, value }) => (
              <div key={label} className="phase-outcomes__item">
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </aside>
      )}
    </section>
  );
}
