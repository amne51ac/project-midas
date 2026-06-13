import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { Star } from '../data/types';
import { padDomainTuple } from '../utils/chartScales';

interface Props {
  stars: Star[];
  colorBy?: 'mv' | 'bv';
}

export function SkyMap({ stars, colorBy = 'mv' }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svg.node()) return;
    svg.selectAll('*').remove();

    const width = svgRef.current!.clientWidth || 520;
    const height = 420;
    const margin = { top: 24, right: 24, bottom: 44, left: 54 };

    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const xExtent = padDomainTuple(d3.extent(stars, (d) => d.x) as [number, number], {
      fraction: 0.08,
      minPad: 48,
    });
    const yExtent = padDomainTuple(d3.extent(stars, (d) => d.y) as [number, number], {
      fraction: 0.08,
      minPad: 48,
    });

    const x = d3.scaleLinear().domain(xExtent).nice().range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain(yExtent).nice().range([height - margin.bottom, margin.top]);

    const colorDomain = d3.extent(stars, (d) => (colorBy === 'mv' ? d.mv : d.bv)) as [number, number];
    // Brighter = bluer-white, dimmer = deep stellar blue (night-sky friendly)
    const color = d3.scaleSequential(d3.interpolateRgb('#4a6a9a', '#eef2ff')).domain(colorDomain);

    const g = svg.append('g');

    // cluster center estimate (from legacy Midas control sheet)
    g.append('circle')
      .attr('cx', x(895))
      .attr('cy', y(650))
      .attr('r', 80)
      .attr('fill', 'none')
      .attr('stroke', '#e8c547')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4 3')
      .attr('opacity', 0.45);

    const tip = tooltipRef.current!;

    g.selectAll('circle')
      .data(stars)
      .join('circle')
      .attr('cx', (d) => x(d.x))
      .attr('cy', (d) => y(d.y))
      .attr('r', 2.5)
      .attr('fill', (d) => color(colorBy === 'mv' ? d.mv : d.bv))
      .attr('opacity', 0.75)
      .on('mouseenter', (event, d) => {
        d3.select(event.currentTarget as SVGCircleElement).attr('r', 5).attr('opacity', 1);
        tip.style.opacity = '1';
        tip.innerHTML = `ID ${d.id}<br/>RA ${d.ra.toFixed(3)}° · Dec ${d.dec.toFixed(3)}°`;
        tip.style.left = `${event.offsetX + 12}px`;
        tip.style.top = `${event.offsetY - 8}px`;
      })
      .on('mouseleave', (event) => {
        d3.select(event.currentTarget as SVGCircleElement).attr('r', 2.5).attr('opacity', 0.75);
        tip.style.opacity = '0';
      });

    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat((v) => `${v}`))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) =>
        sel.selectAll('text').attr('font-family', 'IBM Plex Sans, sans-serif').attr('fill', '#8a98b4'),
      );

    g.append('text')
      .attr('x', width / 2)
      .attr('y', height - 6)
      .attr('text-anchor', 'middle')
      .attr('font-family', 'IBM Plex Sans, sans-serif')
      .attr('font-size', 10)
      .attr('fill', '#9aa8c4')
      .text('Survey X (arcsec offset)');

    g.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) =>
        sel.selectAll('text').attr('font-family', 'IBM Plex Sans, sans-serif').attr('fill', '#8a98b4'),
      );
  }, [stars, colorBy]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} className="chart-svg" role="img" aria-label="Spatial map of survey stars" />
      <div ref={tooltipRef} className="chart-tooltip" />
    </div>
  );
}
