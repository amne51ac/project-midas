import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import diagramData from '../data/methodCompareDiagram.json';
import { finiteValues, padExtent } from '../utils/chartScales';

type CategoryId =
  | 'none'
  | 'mal_only'
  | 'q_only'
  | 'q_mal'
  | 'excel_other'
  | 'other_binary';

const CATEGORY_COUNTS = diagramData.categoryCounts as Record<CategoryId, number>;

const CATEGORY_MAP = Object.fromEntries(
  diagramData.categories.map((c) => [c.id, c]),
) as Record<CategoryId, (typeof diagramData.categories)[number]>;

export function MethodCompareDiagram() {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const { meta, points, categories } = diagramData;

  const [hidden, setHidden] = useState<Set<CategoryId>>(() => new Set(['none']));

  const visiblePoints = useMemo(
    () => points.filter((p) => !hidden.has(p.category as CategoryId)),
    [points, hidden],
  );

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svg.node() || visiblePoints.length === 0) return;
    svg.selectAll('*').remove();

    const width = svgRef.current!.clientWidth || 520;
    const height = 400;
    const margin = { top: 28, right: 24, bottom: 52, left: 56 };
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const bvVals = finiteValues(visiblePoints.map((p) => p.bv0));
    const w2Vals = finiteValues(visiblePoints.map((p) => p.w2Bp));
    const [bvMin, bvMax] = padExtent(Math.min(...bvVals), Math.max(...bvVals), {
      fraction: 0.08,
      minPad: 0.05,
    });
    const [w2Min, w2Max] = padExtent(Math.min(...w2Vals), Math.max(...w2Vals), {
      fraction: 0.1,
      minPad: 0.02,
    });

    const x = d3.scaleLinear().domain([bvMin, bvMax]).range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain([w2Min, w2Max]).range([height - margin.bottom, margin.top]);

    const g = svg.append('g');

    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(8))
      .call((sel) => sel.select('.domain').attr('stroke', 'var(--rule)'))
      .call((sel) => sel.selectAll('.tick line').attr('stroke', 'var(--rule)'))
      .call((sel) => sel.selectAll('.tick text').attr('fill', 'var(--ink-muted)'));

    g.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(7))
      .call((sel) => sel.select('.domain').attr('stroke', 'var(--rule)'))
      .call((sel) => sel.selectAll('.tick line').attr('stroke', 'var(--rule)'))
      .call((sel) => sel.selectAll('.tick text').attr('fill', 'var(--ink-muted)'));

    g.append('text')
      .attr('x', (margin.left + width - margin.right) / 2)
      .attr('y', height - 8)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--ink-muted)')
      .attr('font-size', 12)
      .text(meta.xLabel);

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -(margin.top + height - margin.bottom) / 2)
      .attr('y', 14)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--ink-muted)')
      .attr('font-size', 12)
      .text(meta.yLabel);

    const tooltip = tooltipRef.current;

    const drawOrder: CategoryId[] = [
      'none',
      'other_binary',
      'excel_other',
      'mal_only',
      'q_only',
      'q_mal',
    ];

    for (const catId of drawOrder) {
      const subset = visiblePoints.filter((p) => p.category === catId);
      if (!subset.length) continue;
      const color = CATEGORY_MAP[catId]?.color ?? '#888';
      const r = catId === 'none' ? 2.5 : catId === 'q_mal' ? 5 : 4;
      const opacity = catId === 'none' ? 0.35 : 0.85;

      g.selectAll(`circle.cat-${catId}`)
        .data(subset)
        .join('circle')
        .attr('class', `cat-${catId}`)
        .attr('cx', (d) => x(d.bv0))
        .attr('cy', (d) => y(d.w2Bp))
        .attr('r', r)
        .attr('fill', color)
        .attr('fill-opacity', opacity)
        .attr('stroke', catId === 'q_mal' ? '#fff' : 'none')
        .attr('stroke-width', 0.6)
        .style('cursor', 'default')
        .on('mouseenter', (event, d) => {
          if (!tooltip) return;
          tooltip.hidden = false;
          tooltip.innerHTML = `<strong>Midas #${d.id}</strong><br/>
            bv0 = ${d.bv0.toFixed(3)} · W2−BP = ${d.w2Bp.toFixed(3)}<br/>
            ${d.q ? 'Q · ' : ''}${d.mal ? 'Malofeeva · ' : ''}${d.excel ? 'Excel · ' : ''}${d.ruwe ? 'RUWE' : ''}`;
          tooltip.style.left = `${event.offsetX + 12}px`;
          tooltip.style.top = `${event.offsetY - 8}px`;
        })
        .on('mouseleave', () => {
          if (tooltip) tooltip.hidden = true;
        });
    }
  }, [visiblePoints, meta.xLabel, meta.yLabel]);

  function toggleCategory(id: CategoryId) {
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  if (points.length === 0) {
    return (
      <p className="method-compare__source">
        W2−BP diagram unavailable — run <code>merge_ir_photometry.py</code> and{' '}
        <code>build_web_synthesis.py</code>.
      </p>
    );
  }

  return (
    <div className="method-compare-diagram">
      <div className="method-compare-diagram__legend" role="group" aria-label="Diagram layer toggles">
        {categories.map((cat) => {
          const catId = cat.id as CategoryId;
          const count = CATEGORY_COUNTS[catId] ?? 0;
          const off = hidden.has(catId);
          return (
            <button
              key={cat.id}
              type="button"
              className={`method-compare-diagram__chip${off ? ' method-compare-diagram__chip--off' : ''}`}
              onClick={() => toggleCategory(catId)}
              aria-pressed={!off}
            >
              <span
                className="method-compare-diagram__swatch"
                style={{ background: cat.color }}
                aria-hidden
              />
              {cat.label}
              <span className="method-compare-diagram__chip-count">{count}</span>
            </button>
          );
        })}
      </div>
      <div className="method-compare-diagram__plot">
        <svg ref={svgRef} className="method-compare-diagram__svg" aria-label="W2−BP vs de-reddened B−V" />
        <div ref={tooltipRef} className="method-compare-diagram__tooltip" hidden />
      </div>
      <p className="method-compare__source">
        {meta.nWithIr} Cantat-Gaudin members with AllWISE W2 and Gaia BP (E(B−V) = {meta.ebv}) ·
        Malofeeva IR flags cluster at higher W2−BP; Q-value picks occupy a narrower B−V track
        offset region with partial overlap.
      </p>
    </div>
  );
}
