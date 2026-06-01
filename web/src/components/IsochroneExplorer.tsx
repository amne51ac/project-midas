import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import {
  ISOCHRONE_AGES,
  M34_AGE_GYR,
  turnoffPoint,
  type AgeIsochrone,
  type IsoPoint,
} from '../data/isochrones';
import type { Star } from '../data/types';

const AGE_COLORS: Record<number, string> = {
  0.08: '#6b7c9e',
  0.1: '#8a98b4',
  0.2: '#e8c547',
  0.4: '#c4a86a',
  0.6: '#a8886a',
  1.0: '#8878a8',
};

interface Props {
  stars: Star[];
}

export function IsochroneExplorer({ stars }: Props) {
  const [selected, setSelected] = useState<number[]>([0.1, 0.2, 0.4, 0.6]);
  const svgRef = useRef<SVGSVGElement>(null);

  const activeIsochrones = useMemo(
    () => ISOCHRONE_AGES.filter((a) => selected.includes(a.ageGyr)),
    [selected],
  );

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svg.node()) return;
    svg.selectAll('*').remove();

    const width = svgRef.current!.clientWidth || 640;
    const height = 380;
    const margin = { top: 24, right: 20, bottom: 44, left: 52 };

    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const x = d3.scaleLinear().domain([-0.05, 1.45]).range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain([12.5, 0.5]).range([height - margin.bottom, margin.top]);

    const g = svg.append('g');

    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(7))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) => sel.selectAll('text').attr('fill', '#8a98b4').attr('font-size', 10));

    g.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(7))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) => sel.selectAll('text').attr('fill', '#8a98b4').attr('font-size', 10));

    g.append('text')
      .attr('x', width / 2)
      .attr('y', height - 10)
      .attr('text-anchor', 'middle')
      .attr('fill', '#9aa8c4')
      .attr('font-size', 10)
      .text('B − V');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -(height / 2))
      .attr('y', 14)
      .attr('text-anchor', 'middle')
      .attr('fill', '#9aa8c4')
      .attr('font-size', 10)
      .text('Mv');

    const line = d3
      .line<IsoPoint>()
      .x((d) => x(d.bv))
      .y((d) => y(d.mv));

    activeIsochrones.forEach((iso) => {
      const color = AGE_COLORS[iso.ageGyr] ?? '#888';
      const isBest = iso.ageGyr === M34_AGE_GYR;
      g.append('path')
        .datum(iso.points)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', isBest ? 2.8 : 1.6)
        .attr('stroke-dasharray', isBest ? null : '5 4')
        .attr('opacity', isBest ? 1 : 0.8)
        .attr('d', line);

      const to = turnoffPoint(iso.points);
      g.append('circle')
        .attr('cx', x(to.bv))
        .attr('cy', y(to.mv))
        .attr('r', isBest ? 4.5 : 3)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 1.2);
    });

    g.selectAll('circle.star')
      .data(stars)
      .join('circle')
      .attr('class', 'star')
      .attr('cx', (d) => x(d.bv))
      .attr('cy', (d) => y(d.mv))
      .attr('r', 2.2)
      .attr('fill', '#eef2ff')
      .attr('opacity', 0.35);

    const legendX = width - margin.right;
    let legendY = margin.top;
    activeIsochrones.forEach((iso) => {
      const color = AGE_COLORS[iso.ageGyr] ?? '#888';
      g.append('line')
        .attr('x1', legendX - 48)
        .attr('x2', legendX - 28)
        .attr('y1', legendY)
        .attr('y2', legendY)
        .attr('stroke', color)
        .attr('stroke-width', iso.ageGyr === M34_AGE_GYR ? 2.5 : 1.5);
      g.append('text')
        .attr('x', legendX - 24)
        .attr('y', legendY + 3)
        .attr('fill', '#9aa8c4')
        .attr('font-size', 9)
        .text(iso.shortLabel);
      legendY += 14;
    });
  }, [stars, activeIsochrones]);

  const toggleAge = (ageGyr: number) => {
    setSelected((prev) => {
      if (prev.includes(ageGyr)) {
        return prev.length > 1 ? prev.filter((a) => a !== ageGyr) : prev;
      }
      return [...prev, ageGyr].sort((a, b) => a - b);
    });
  };

  return (
    <div className="iso-explorer">
      <div className="iso-explorer__header">
        <h3 className="iso-explorer__title">Isochrone gallery</h3>
        <p className="iso-explorer__intro">
          Toggle ages to see how the Yonsei–Yale model shifts on the HR diagram. Open clusters of
          different ages share the same chemistry but different turnoffs — the bend where stars leave
          the main sequence. M34 matches the <strong>200 Myr</strong> track (gold).
        </p>
      </div>

      <div className="iso-explorer__chips" role="group" aria-label="Select isochrone ages">
        {ISOCHRONE_AGES.map((iso) => {
          const on = selected.includes(iso.ageGyr);
          return (
            <button
              key={iso.ageGyr}
              type="button"
              className={`iso-explorer__chip${on ? ' is-active' : ''}${iso.ageGyr === M34_AGE_GYR ? ' is-m34' : ''}`}
              aria-pressed={on}
              onClick={() => toggleAge(iso.ageGyr)}
              style={{ '--chip-color': AGE_COLORS[iso.ageGyr] } as React.CSSProperties}
            >
              {iso.label}
            </button>
          );
        })}
      </div>

      <div className="iso-explorer__chart">
        <svg ref={svgRef} className="chart-svg" role="img" aria-label="Interactive isochrone comparison" />
      </div>

      <div className="iso-explorer__cards">
        {activeIsochrones.map((iso) => (
          <IsoCard key={iso.ageGyr} iso={iso} isBest={iso.ageGyr === M34_AGE_GYR} />
        ))}
      </div>
    </div>
  );
}

function IsoCard({ iso, isBest }: { iso: AgeIsochrone; isBest: boolean }) {
  const to = turnoffPoint(iso.points);
  return (
    <article className={`iso-explorer__card${isBest ? ' iso-explorer__card--best' : ''}`}>
      <header>
        <span className="iso-explorer__card-age" style={{ color: AGE_COLORS[iso.ageGyr] }}>
          {iso.label}
        </span>
        {isBest && <span className="iso-explorer__badge">M34 fit</span>}
      </header>
      <p>{iso.note}</p>
      <dl className="iso-explorer__stats">
        <div>
          <dt>Turnoff Mv</dt>
          <dd>{to.mv.toFixed(2)}</dd>
        </div>
        <div>
          <dt>Turnoff B−V</dt>
          <dd>{to.bv.toFixed(2)}</dd>
        </div>
      </dl>
    </article>
  );
}
