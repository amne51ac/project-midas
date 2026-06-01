import { ECOSYSTEM_TOOLS, STATUS_LABELS, TOOL_CATEGORIES, type ToolStatus } from '../data/toolsInventory';

const STATUS_CLASS: Record<ToolStatus, string> = {
  ready: 'tool-card__status--ready',
  partial: 'tool-card__status--partial',
  adapt: 'tool-card__status--adapt',
  build: 'tool-card__status--build',
  replace: 'tool-card__status--replace',
};

function StatusLegend() {
  const items: ToolStatus[] = ['ready', 'partial', 'adapt', 'build', 'replace'];
  return (
    <div className="tools-legend" aria-label="Tool status legend">
      {items.map((status) => (
        <span key={status} className={`tools-legend__item ${STATUS_CLASS[status]}`}>
          {STATUS_LABELS[status]}
        </span>
      ))}
    </div>
  );
}

export function ToolsInventory() {
  return (
    <div className="tools-inventory">
      <div className="section__prose tools-inventory__intro">
        <p className="lead">
          Completing Project Midas is not one program — it is a toolchain. Some pieces already exist in
          the legacy archive or the public literature; others are partially built in this repository; several
          critical joins and validation steps still need to be written.
        </p>
        <p>
          The inventory below rates each component against our actual research plan: what we have today,
          whether it meets current scientific standards, what gap remains, and which project phase it
          belongs to. <strong>Ready</strong> means use as-is. <strong>Adapt</strong> and{' '}
          <strong>Partial</strong> mean existing assets that need engineering or modernization.{' '}
          <strong>Build</strong> means net-new code. <strong>Supersede</strong> marks legacy items we keep
          for comparison but no longer rely on.
        </p>
      </div>

      <StatusLegend />

      {TOOL_CATEGORIES.map((category) => (
        <section key={category.id} className="tools-category">
          <h3 className="tools-category__title">{category.title}</h3>
          <p className="tools-category__summary">{category.summary}</p>
          <div className="tools-category__grid">
            {category.tools.map((tool) => (
              <article key={tool.id} className="tool-card">
                <header className="tool-card__header">
                  <h4 className="tool-card__name">{tool.name}</h4>
                  <span className={`tool-card__status ${STATUS_CLASS[tool.status]}`}>
                    {STATUS_LABELS[tool.status]}
                  </span>
                </header>
                <dl className="tool-card__dl">
                  <div>
                    <dt>What exists</dt>
                    <dd>{tool.exists}</dd>
                  </div>
                  <div>
                    <dt>Does it meet our needs?</dt>
                    <dd>{tool.fit}</dd>
                  </div>
                  <div>
                    <dt>Gap</dt>
                    <dd>{tool.gap}</dd>
                  </div>
                  <div>
                    <dt>Action</dt>
                    <dd>{tool.action}</dd>
                  </div>
                </dl>
                <footer className="tool-card__phase">{tool.phase}</footer>
              </article>
            ))}
          </div>
        </section>
      ))}

      <section className="tools-ecosystem">
        <h3 className="tools-category__title">Supporting ecosystem (not owned by this project)</h3>
        <p className="tools-category__summary">
          These external tools are part of the expected workflow. We do not maintain them, but the pipeline
          should interoperate with them rather than reinventing their functionality.
        </p>
        <ul className="tools-ecosystem__list">
          {ECOSYSTEM_TOOLS.map((tool) => (
            <li key={tool.name}>
              <strong>{tool.name}</strong> — {tool.role}. <em>{tool.note}</em>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
