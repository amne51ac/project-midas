import type { HistoryEvent } from '../data/types';

export function HistoryTimeline({ events }: { events: HistoryEvent[] }) {
  return (
    <div className="timeline" role="list">
      {events.map((ev) => (
        <article key={ev.title} className="timeline__item" role="listitem">
          <div className="timeline__year">{ev.year}</div>
          <div className="timeline__era">{ev.era}</div>
          <h3 className="timeline__title">{ev.title}</h3>
          <p className="timeline__summary">{ev.summary}</p>
        </article>
      ))}
    </div>
  );
}
