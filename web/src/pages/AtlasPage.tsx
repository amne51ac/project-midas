import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { CredenceAtlas } from '../components/CredenceAtlas';
import atlasBundle from '../data/atlasT0.json';
import type { AtlasBundle } from '../data/atlasTypes';

const bundle = atlasBundle as AtlasBundle;

export function AtlasPage() {
  return (
    <>
      <Header />
      <main className="atlas-page">
        <div className="atlas-page__hero section">
          <p className="section__label">Credence · Display</p>
          <h1 className="atlas-page__title">Credence Atlas</h1>
          <p className="atlas-page__lede lead">
            T0 benchmark clusters — {bundle.meta.nStars.toLocaleString()} Cantat-Gaudin members
            colored by infer output. Pan the sky in RA/Dec; toggle clusters and filter by{' '}
            <code>p_binary</code>. Model trained with cluster-held-out evaluation (M34 not in
            training when holdout F1 is reported).
          </p>
          <p className="findings-section__link">
            <a href="/credence">Credence overview</a>
            {' · '}
            <a href="/credence#ml-plan">ML data plan</a>
          </p>
        </div>
        <section className="section section--rule">
          <CredenceAtlas bundle={bundle} />
        </section>
      </main>
      <Footer />
    </>
  );
}

export default AtlasPage;
