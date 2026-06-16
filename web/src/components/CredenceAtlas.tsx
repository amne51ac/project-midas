import { Suspense, useCallback, useMemo, useRef, useState, type MutableRefObject } from 'react';
import { Canvas } from '@react-three/fiber';
import type { AtlasBundle } from '../data/atlasTypes';
import { ATLAS_CONSTELLATIONS, ATLAS_REFERENCE_OBJECTS } from '../data/atlasSkyOverlay';
import { AtlasScene } from './atlas/AtlasScene';
import { AtlasSciencePanel } from './atlas/AtlasSciencePanel';
import { AtlasStarDetail } from './atlas/AtlasStarDetail';
import type { AtlasPick } from './atlas/atlasPickTypes';

type ColorMode = 'pBinary' | 'pMember' | 'malofeeva';

interface Props {
  bundle: AtlasBundle;
}

export function CredenceAtlas({ bundle }: Props) {
  const [activeClusters, setActiveClusters] = useState<Set<string>>(
    () => new Set(bundle.clusters.map((c) => c.id)),
  );
  const [colorMode, setColorMode] = useState<ColorMode>('pBinary');
  const [minPBinary, setMinPBinary] = useState(0);
  const [hover, setHover] = useState<AtlasPick | null>(null);
  const [selected, setSelected] = useState<AtlasPick | null>(null);
  const [showConstellations, setShowConstellations] = useState(true);
  const [showBrightStars, setShowBrightStars] = useState(true);
  const [controlsOpen, setControlsOpen] = useState(true);
  const [scienceOpen, setScienceOpen] = useState(false);
  const [flyTarget, setFlyTarget] = useState<{ ra: number; dec: number } | null>(null);
  const labelPortal = useRef<HTMLDivElement>(null) as MutableRefObject<HTMLDivElement>;

  const visible = useMemo(
    () =>
      bundle.stars.filter(
        (s) => activeClusters.has(s.clusterId) && s.pBinary >= minPBinary,
      ),
    [bundle.stars, activeClusters, minPBinary],
  );

  const detailPick = selected ?? hover;

  const showClusters = activeClusters.size > 0;

  const toggleAllClusters = () => {
    setActiveClusters((prev) =>
      prev.size > 0 ? new Set() : new Set(bundle.clusters.map((c) => c.id)),
    );
  };

  const flyToCluster = useCallback(
    (clusterId: string) => {
      const cluster = bundle.clusters.find((c) => c.id === clusterId);
      if (!cluster) return;
      setFlyTarget({ ra: cluster.ra, dec: cluster.dec });
    },
    [bundle.clusters],
  );

  const resetView = useCallback(() => {
    setFlyTarget({ ra: 0, dec: 0 });
  }, []);

  const handleSelect = useCallback((pick: AtlasPick | null) => {
    setSelected(pick);
  }, []);

  return (
    <div
      className={`atlas-immersive${scienceOpen ? ' atlas-immersive--science-open' : ''}${selected ? ' atlas-immersive--detail-open' : ''}`}
    >
      <div ref={labelPortal} className="atlas-immersive__labels" aria-hidden />

      <Canvas
        className="atlas-immersive__canvas"
        camera={{ position: [0, 0, 0], fov: 68, near: 0.1, far: SKY_FAR }}
        gl={{ antialias: true, powerPreference: 'high-performance' }}
        dpr={[1, 2]}
      >
        <Suspense fallback={null}>
          <AtlasScene
            bundle={bundle}
            visible={visible}
            activeClusters={activeClusters}
            colorMode={colorMode}
            flyTarget={flyTarget}
            onFlyComplete={() => setFlyTarget(null)}
            onHover={setHover}
            onSelect={handleSelect}
            showConstellations={showConstellations}
            showBrightStars={showBrightStars}
            brightStars={ATLAS_REFERENCE_OBJECTS}
            constellations={ATLAS_CONSTELLATIONS}
            labelPortal={labelPortal}
          />
        </Suspense>
      </Canvas>

      <div className="atlas-immersive__vignette" aria-hidden />

      <header className="atlas-immersive__header">
        <div className="atlas-immersive__header-main">
          <p className="section__label">Credence · Display</p>
          <h1 className="atlas-immersive__title">Credence Atlas</h1>
          <p className="atlas-immersive__tagline">
            {visible.length.toLocaleString()} cluster members · drag to look · scroll to zoom · click
            a star for details
          </p>
        </div>
        <div className="atlas-immersive__header-actions">
          <button
            type="button"
            className="atlas-panel__btn"
            onClick={() => setControlsOpen((v) => !v)}
            aria-expanded={controlsOpen}
          >
            {controlsOpen ? 'Hide controls' : 'Show controls'}
          </button>
        </div>
      </header>

      {detailPick && (
        <AtlasStarDetail
          pick={detailPick}
          clusters={bundle.clusters}
          pinned={selected != null}
          onClose={() => setSelected(null)}
        />
      )}

      <aside className={`atlas-immersive__controls${controlsOpen ? '' : ' atlas-immersive__controls--hidden'}`}>
        <div className="atlas-immersive__controls-sky">
          <fieldset className="atlas-panel__fieldset">
            <legend>Sky layers</legend>
            <label className="atlas-panel__check">
              <input
                type="checkbox"
                checked={showConstellations}
                onChange={() => setShowConstellations((v) => !v)}
              />
              Constellations
            </label>
            <label className="atlas-panel__check">
              <input
                type="checkbox"
                checked={showBrightStars}
                onChange={() => setShowBrightStars((v) => !v)}
              />
              Named stars
            </label>
            <label className="atlas-panel__check">
              <input type="checkbox" checked={showClusters} onChange={toggleAllClusters} />
              Clusters
            </label>
          </fieldset>
          <details className="atlas-panel__details">
            <summary className="atlas-panel__details-summary">Fly to</summary>
            <div className="atlas-panel__details-body">
              {bundle.clusters.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className="atlas-panel__fly"
                  onClick={() => flyToCluster(c.id)}
                >
                  {c.name}
                </button>
              ))}
            </div>
          </details>
          <label className="atlas-panel__field">
            Color
            <select value={colorMode} onChange={(e) => setColorMode(e.target.value as ColorMode)}>
              <option value="pBinary">p_binary (infer)</option>
              <option value="pMember">P(member) ingest</option>
              <option value="malofeeva">Malofeeva (M34)</option>
            </select>
          </label>
          <label className="atlas-panel__field">
            Min p_binary {minPBinary.toFixed(2)}
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={minPBinary}
              onChange={(e) => setMinPBinary(Number(e.target.value))}
            />
          </label>
          <div className="atlas-panel__actions">
            <button type="button" className="atlas-panel__reset" onClick={resetView}>
              Reset view
            </button>
          </div>
        </div>

        <button
          type="button"
          className="atlas-science-panel__toggle"
          onClick={() => setScienceOpen((v) => !v)}
          aria-expanded={scienceOpen}
        >
          <span>{scienceOpen ? 'Hide infer summary' : 'Show infer summary'}</span>
          <span className="atlas-science-panel__toggle-hint" aria-hidden>
            {scienceOpen ? '▾' : '▸'}
          </span>
        </button>

        {scienceOpen && (
          <AtlasSciencePanel
            stars={visible}
            clusters={bundle.clusters}
            activeClusters={activeClusters}
            minPBinary={minPBinary}
            meta={bundle.meta}
          />
        )}
      </aside>

      <footer className="atlas-immersive__credit">
        Sky: NASA/GSFC SVS · Tycho Catalog Skymap
      </footer>
    </div>
  );
}

const SKY_FAR = 1000;
