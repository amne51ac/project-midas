import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { AtlasBundle, AtlasStar } from '../data/atlasTypes';
import { padDomainTuple } from '../utils/chartScales';

type ColorMode = 'pBinary' | 'pMember' | 'malofeeva';

interface Props {
  bundle: AtlasBundle;
}

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
  const tooltipRef = useRef<HTMLDivElement>(null);
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

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svg.node() || visible.length === 0) return;
    svg.selectAll('*').remove();

    const width = svgRef.current!.clientWidth || 720;
    const height = 520;
    const margin = { top: 20, right: 16, bottom: 44, left: 52 };
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const xDomain = padDomainTuple(d3.extent(visible, (s) => s.ra) as [number, number], {
      fraction: 0.06,
      minPad: 0.05,
    });
    const yDomain = padDomainTuple(d3.extent(visible, (s) => s.dec) as [number, number], {
      fraction: 0.06,
      minPad: 0.05,
    });

    const x = d3.scaleLinear().domain(xDomain).nice().range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain(yDomain).nice().range([height - margin.bottom, margin.top]);

    const g = svg.append('g');

    bundle.clusters
      .filter((c) => activeClusters.has(c.id))
      .forEach((c) => {
        g.append('circle')
          .attr('cx', x(c.ra))
          .attr('cy', y(c.dec))
          .attr('r', x(c.radiusDeg) - x(0))
          .attr('fill', 'none')
          .attr('stroke', '#334155')
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '4 3')
          .attr('opacity', 0.5);
      });

    g.selectAll('circle.star')
      .data(visible)
      .join('circle')
      .attr('class', 'star')
      .attr('cx', (s) => x(s.ra))
      .attr('cy', (s) => y(s.dec))
      .attr('r', (s) => starRadius(s.g))
      .attr('fill', (s) => starColor(s, colorMode))
      .attr('fill-opacity', 0.85)
      .attr('stroke', '#0f172a')
      .attr('stroke-width', 0.3)
      .style('cursor', 'pointer')
      .on('mouseenter', (_, s) => setHover(s))
      .on('mouseleave', () => setHover(null));

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(8))
      .append('text')
      .attr('x', width / 2)
      .attr('y', 36)
      .attr('fill', '#94a3b8')
      .attr('text-anchor', 'middle')
      .attr('font-size', 11)
      .text('RA (deg)');

    svg
      .append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(8))
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -40)
      .attr('fill', '#94a3b8')
      .attr('text-anchor', 'middle')
      .attr('font-size', 11)
      .text('Dec (deg)');
  }, [visible, colorMode, activeClusters, bundle.clusters]);

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
        <p className="atlas-panel__meta">
          {visible.length.toLocaleString()} stars · {bundle.meta.modelVersion}
          {bundle.meta.holdoutF1 != null && (
            <> · M34 holdout F1 {bundle.meta.holdoutF1.toFixed(2)}</>
          )}
        </p>
      </div>
      <div className="atlas-panel__chart-wrap">
        <svg ref={svgRef} className="atlas-panel__svg" role="img" aria-label="T0 cluster sky map" />
        <div ref={tooltipRef} className={`atlas-tooltip${hover ? ' atlas-tooltip--visible' : ''}`}>
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
