import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { FINDINGS } from '../data/findings';

export function FindingsPage() {
  const { headline, lede, atAGlance, sections, limitations, openQuestions } = FINDINGS;

  return (
    <>
      <Header />
      <main className="findings-page">
        <div className="findings-page__hero section">
          <p className="section__label">Synthesis</p>
          <h1 className="findings-page__title">{headline}</h1>
          <p className="findings-page__lede lead">{lede}</p>
        </div>

        <section className="findings-page__glance section section--rule" aria-label="Key numbers">
          <h2 className="section__subhead">At a glance</h2>
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
            <h2 className="findings-section__title">{block.title}</h2>
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

        <section className="findings-page__closing section section--rule">
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

export default FindingsPage;
