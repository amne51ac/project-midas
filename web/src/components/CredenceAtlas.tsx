import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { AtlasBundle, AtlasStar } from '../data/atlasTypes';
import { padDomainTuple } from '../utils/chartScales';

type ColorMode = 'pBinary' | 'pMember' | 'malofeeva';

interface Props {
  bundle: AtlasBundle;
}

const MARGIN = { top: 20, right: 16, bottom: 44, left: 52 };
const CHART_HEIGHT = 520;

function starColor(star: AtlasStar, mode: ColorMode): string {
  if (mode === 'malofeeva') return star.malofeeva ? '#f59e0b' : '#64748b';
  const t = mode === 'pBinary' ? star.pBinary : (star.pMember ?? 0);
  return d3.interpolatePlasma(Math.min(1, Math.max(0, t)));
}

function starRadius(g: number | undefined): number {
  if (g == null) return 2.5;
  return d3.scaleLinear().domain([8, 18]).range([4.5, 1.8]).clamp(true)(g);
}

export function CredenceAtlas({ bundle }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const transformRef = useRef<d3.ZoomTransform>(d3.zoomIdentity);
  const [activeClusters, setActiveClusters] = useState<Set<string>>(
    () => new Set(bundle.clusters.map((c) => c.id)),
  );
  const [colorMode, setColorMode] = useState<ColorMode>('pBinary');
  const [minPBinary, setMinPBinary] = useState(0);
  const [hover, setHover] = useState<AtlasStar | null>(null);

  const visible = useMemo(
    () =>
      bundle.stars.filter(
        (s) => activeClusters.has(s.clusterId) && s.pBinary >= minPBinary,
      ),
    [bundle.stars, activeClusters, minPBinary],
  );

  const toggleCluster = (id: string) => {
    setActiveClusters((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const flyToCluster = useCallback(
    (clusterId: string) => {
      const svg = svgRef.current;
      const zoom = zoomRef.current;
      const cluster = bundle.clusters.find((c) => c.id === clusterId);
      if (!svg || !zoom || !cluster || visible.length === 0) return;

      const width = svg.clientWidth || 720;
      const height = CHART_HEIGHT;
      const xDomain = padDomainTuple(d3.extent(visible, (s) => s.ra) as [number, number], {
        fraction: 0.06,
        minPad: 0.05,
      });
      const yDomain = padDomainTuple(d3.extent(visible, (s) => s.dec) as [number, number], {
        fraction: 0.06,
        minPad: 0.05,
      });
      const x0 = d3
        .scaleLinear()
        .domain(xDomain)
        .nice()
        .range([MARGIN.left, width - MARGIN.right]);
      const y0 = d3
        .scaleLinear()
        .domain(yDomain)
        .nice()
        .range([height - MARGIN.bottom, MARGIN.top]);

      const span = Math.max(cluster.radiusDeg * 2.8, 0.15);
      const k = Math.min(
        (width - MARGIN.left - MARGIN.right) / span,
        (height - MARGIN.top - MARGIN.bottom) / span,
        40,
      );
      const cx = x0(cluster.ra);
      const cy = y0(cluster.dec);
      const transform = d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(k)
        .translate(-cx, -cy);

      d3.select(svg).transition().duration(650).call(zoom.transform as never, transform);
    },
    [bundle.clusters, visible],
  );

  const resetView = useCallback(() => {
    const svg = svgRef.current;
    const zoom = zoomRef.current;
    if (!svg || !zoom) return;
    d3.select(svg).transition().duration(400).call(zoom.transform as never, d3.zoomIdentity);
  }, []);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svg.node() || visible.length === 0) return;
    svg.selectAll('*').remove();
    transformRef.current = d3.zoomIdentity;

    const width = svgRef.current!.clientWidth || 720;
    const height = CHART_HEIGHT;
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const xDomain = padDomainTuple(d3.extent(visible, (s) => s.ra) as [number, number], {
      fraction: 0.06,
      minPad: 0.05,
    });
    const yDomain = padDomainTuple(d3.extent(visible, (s) => s.dec) as [number, number], {
      fraction: 0.06,
      minPad: 0.05,
    });

    const x0 = d3
      .scaleLinear()
      .domain(xDomain)
      .nice()
      .range([MARGIN.left, width - MARGIN.right]);
    const y0 = d3
      .scaleLinear()
      .domain(yDomain)
      .nice()
      .range([height - MARGIN.bottom, MARGIN.top]);

    svg
      .append('defs')
      .append('clipPath')
      .attr('id', 'atlas-clip')
      .append('rect')
      .attr('x', MARGIN.left)
      .attr('y', MARGIN.top)
      .attr('width', width - MARGIN.left - MARGIN.right)
      .attr('height', height - MARGIN.top - MARGIN.bottom);

    const gPlot = svg.append('g').attr('clip-path', 'url(#atlas-clip)');
    const gHulls = gPlot.append('g').attr('class', 'atlas-hulls');
    const gStars = gPlot.append('g').attr('class', 'atlas-stars');

    const gX = svg
      .append('g')
      .attr('class', 'atlas-axis-x')
      .attr('transform', `translate(0,${height - MARGIN.bottom})`);
    const gY = svg.append('g').attr('class', 'atlas-axis-y').attr('transform', `translate(${MARGIN.left},0)`);

    gX
      .append('text')
      .attr('x', width / 2)
      .attr('y', 36)
      .attr('fill', '#94a3b8')
      .attr('text-anchor', 'middle')
      .attr('font-size', 11)
      .text('RA (deg)');

    gY
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -40)
      .attr('fill', '#94a3b8')
      .attr('text-anchor', 'middle')
      .attr('font-size', 11)
      .text('Dec (deg)');

    const activeHulls = bundle.clusters.filter((c) => activeClusters.has(c.id));

    gHulls
      .selectAll('circle.hull')
      .data(activeHulls)
      .join('circle')
      .attr('class', 'hull')
      .attr('fill', 'none')
      .attr('stroke', '#334155')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4 3')
      .attr('opacity', 0.5);

    gStars
      .selectAll('circle.star')
      .data(visible)
      .join('circle')
      .attr('class', 'star')
      .attr('r', (s) => starRadius(s.g))
      .attr('fill', (s) => starColor(s, colorMode))
      .attr('fill-opacity', 0.85)
      .attr('stroke', '#0f172a')
      .attr('stroke-width', 0.3)
      .style('cursor', 'pointer')
      .on('mouseenter', (_, s) => setHover(s))
      .on('mouseleave', () => setHover(null));

    const draw = (transform: d3.ZoomTransform) => {
      transformRef.current = transform;
      const x = transform.rescaleX(x0);
      const y = transform.rescaleY(y0);

      gHulls
        .selectAll<SVGCircleElement, (typeof activeHulls)[0]>('circle.hull')
        .attr('cx', (c) => x(c.ra))
        .attr('cy', (c) => y(c.dec))
        .attr('r', (c) => Math.abs(x(c.ra + c.radiusDeg) - x(c.ra)));

      gStars
        .selectAll<SVGCircleElement, AtlasStar>('circle.star')
        .attr('cx', (s) => x(s.ra))
        .attr('cy', (s) => y(s.dec));

      gX.call(d3.axisBottom(x).ticks(8));
      gY.call(d3.axisLeft(y).ticks(8));
    };

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 48])
      .translateExtent([
        [MARGIN.left - width, MARGIN.top - height],
        [width * 2 - MARGIN.right, height * 2 - MARGIN.bottom],
      ])
      .on('zoom', (event) => draw(event.transform));

    zoomRef.current = zoom;
    svg.call(zoom as (sel: typeof svg) => void).on('dblclick.zoom', null);
    draw(d3.zoomIdentity);

    return () => {
      svg.on('.zoom', null);
      zoomRef.current = null;
    };
  }, [visible, activeClusters, bundle.clusters, colorMode]);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    d3.select(svg)
      .selectAll<SVGCircleElement, AtlasStar>('circle.star')
      .attr('fill', (s) => starColor(s, colorMode));
  }, [colorMode]);

  return (
    <div className="atlas-panel">
      <div className="atlas-panel__controls">
        <fieldset className="atlas-panel__fieldset">
          <legend>Clusters</legend>
          {bundle.clusters.map((c) => (
            <label key={c.id} className="atlas-panel__check">
              <input
                type="checkbox"
                checked={activeClusters.has(c.id)}
                onChange={() => toggleCluster(c.id)}
              />
              {c.name}
            </label>
          ))}
        </fieldset>
        <fieldset className="atlas-panel__fieldset">
          <legend>Fly to</legend>
          {bundle.clusters.map((c) => (
            <button
              key={c.id}
              type="button"
              className="atlas-panel__fly"
              disabled={!activeClusters.has(c.id)}
              onClick={() => flyToCluster(c.id)}
            >
              {c.name}
            </button>
          ))}
        </fieldset>
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
        <p className="atlas-panel__meta">
          {visible.length.toLocaleString()} stars · drag to pan · scroll to zoom ·{' '}
          {bundle.meta.modelVersion}
          {bundle.meta.holdoutF1 != null && (
            <> · M34 holdout F1 {bundle.meta.holdoutF1.toFixed(2)}</>
          )}
        </p>
      </div>
      <div className="atlas-panel__chart-wrap">
        <svg ref={svgRef} className="atlas-panel__svg" role="img" aria-label="T0 cluster sky map" />
        <div className={`atlas-tooltip${hover ? ' atlas-tooltip--visible' : ''}`}>
          {hover && (
            <>
              <strong>{hover.clusterId}</strong>
              <br />
              RA {hover.ra.toFixed(3)}°, Dec {hover.dec.toFixed(3)}°
              <br />
              p_binary {hover.pBinary.toFixed(3)}
              {hover.pMember != null && (
                <>
                  <br />
                  P(member) {hover.pMember.toFixed(2)}
                </>
              )}
              {hover.malofeeva ? <br /> : null}
              {hover.malofeeva ? 'Malofeeva IR' : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
