import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { Star } from '../data/types';
import type { AgeIsochrone, IsoPoint } from '../data/isochrones';
import { PARSEC_COMPARE_AGES, PARSEC_M34 } from '../data/parsecIsochrones';
import { turnoffPoint } from '../data/isochrones';

export type HRDiagramMode =
  | 'stars'
  | 'main-sequence'
  | 'isochrone-intro'
  | 'age-compare'
  | 'age-fit'
  | 'binary';

interface Props {
  stars: Star[];
  isochrone: IsoPoint[];
  ageIsochrones?: AgeIsochrone[];
  compareAges?: AgeIsochrone[];
  mode?: HRDiagramMode;
  highlight?: 'single' | 'binary' | 'all';
}

const AGE_COLORS: Record<number, string> = {
  0.08: '#6b7c9e',
  0.1: '#8a98b4',
  0.2: '#e8c547',
  0.4: '#c4a86a',
  0.6: '#a8886a',
  1.0: '#8878a8',
};

const PARSEC_COLOR = '#67c4e8';

export function HRDiagram({
  stars,
  isochrone,
  ageIsochrones = [],
  compareAges,
  mode = 'stars',
  highlight = 'all',
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svg.node()) return;
    svg.selectAll('*').remove();

    const width = svgRef.current!.clientWidth || 520;
    const height = 420;
    const margin = { top: 28, right: 24, bottom: 48, left: 56 };

    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const x = d3.scaleLinear().domain([-0.1, 1.4]).range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain([13, 2]).range([height - margin.bottom, margin.top]);

    const g = svg.append('g');

    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(8))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) =>
        sel.selectAll('text').attr('font-family', 'Libre Franklin, sans-serif').attr('font-size', 10).attr('fill', '#8a98b4'),
      );

    g.append('text')
      .attr('x', width / 2)
      .attr('y', height - 8)
      .attr('text-anchor', 'middle')
      .attr('font-family', 'Libre Franklin, sans-serif')
      .attr('font-size', 11)
      .attr('fill', '#9aa8c4')
      .text('B − V  →  hotter / bluer');

    g.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(8))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) =>
        sel.selectAll('text').attr('font-family', 'Libre Franklin, sans-serif').attr('font-size', 10).attr('fill', '#8a98b4'),
      );

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -(height / 2))
      .attr('y', 16)
      .attr('text-anchor', 'middle')
      .attr('font-family', 'Libre Franklin, sans-serif')
      .attr('font-size', 11)
      .attr('fill', '#9aa8c4')
      .text('Mv  ↑  brighter');

    const isoLine = d3
      .line<IsoPoint>()
      .x((d) => x(d.bv))
      .y((d) => y(d.mv));

    const drawIso = (points: IsoPoint[], stroke: string, widthPx: number, dash?: string, opacity = 1) => {
      g.append('path')
        .datum(points)
        .attr('fill', 'none')
        .attr('stroke', stroke)
        .attr('stroke-width', widthPx)
        .attr('stroke-dasharray', dash ?? null)
        .attr('opacity', opacity)
        .attr('d', isoLine);
    };

    const showAgeCompare = mode === 'age-compare' || mode === 'age-fit';
    const compareSet = compareAges ?? ageIsochrones;
    const primaryIso =
      ageIsochrones.find((a) => a.ageGyr === 0.2)?.points ?? isochrone;

    if (showAgeCompare && compareSet.length) {
      compareSet.forEach((ageIso) => {
        const isPrimary = mode === 'age-fit' && ageIso.ageGyr === 0.2;
        const isBackground = mode === 'age-fit' && ageIso.ageGyr !== 0.2;
        drawIso(
          ageIso.points,
          AGE_COLORS[ageIso.ageGyr] ?? '#888',
          isPrimary ? 2.8 : mode === 'age-compare' ? 2 : 1.4,
          isBackground ? '4 4' : undefined,
          isPrimary ? 1 : mode === 'age-compare' ? 0.85 : 0.45,
        );
        if (mode === 'age-compare' && ageIso.points.length) {
          const to = turnoffPoint(ageIso.points);
          g.append('circle')
            .attr('cx', x(to.bv))
            .attr('cy', y(to.mv))
            .attr('r', ageIso.ageGyr === 0.2 ? 5 : 3.5)
            .attr('fill', 'none')
            .attr('stroke', AGE_COLORS[ageIso.ageGyr] ?? '#888')
            .attr('stroke-width', 1.2);
        }
      });

      const parsecSet =
        mode === 'age-compare'
          ? PARSEC_COMPARE_AGES.filter((p) => compareSet.some((c) => c.ageGyr === p.ageGyr))
          : [PARSEC_M34];

      parsecSet.forEach((ageIso) => {
        const isPrimary = mode === 'age-fit';
        drawIso(
          ageIso.points,
          PARSEC_COLOR,
          isPrimary ? 2.2 : 1.4,
          '4 3',
          isPrimary ? 0.9 : 0.55,
        );
      });
    } else if (mode !== 'stars') {
      drawIso(primaryIso, '#e8c547', mode === 'isochrone-intro' ? 2 : 2.5);
    }

    if (mode === 'main-sequence' || mode === 'isochrone-intro' || mode === 'age-fit') {
      g.append('text')
        .attr('x', x(0.55))
        .attr('y', y(4.2))
        .attr('font-family', 'Libre Franklin, sans-serif')
        .attr('font-size', 10)
        .attr('font-weight', 600)
        .attr('fill', '#9aa8c4')
        .attr('opacity', 0.85)
        .text('main sequence');
    }

    if (mode === 'age-fit' && primaryIso.length > 2) {
      const turnoff = turnoffPoint(primaryIso);
      g.append('circle')
        .attr('cx', x(turnoff.bv))
        .attr('cy', y(turnoff.mv))
        .attr('r', 5)
        .attr('fill', 'none')
        .attr('stroke', '#e8c547')
        .attr('stroke-width', 1.5);
      g.append('text')
        .attr('x', x(turnoff.bv) + 10)
        .attr('y', y(turnoff.mv) + 4)
        .attr('font-family', 'Libre Franklin, sans-serif')
        .attr('font-size', 9)
        .attr('fill', '#e8c547')
        .text('turnoff ~2 M☉ (YY)');

      const pTurnoff = turnoffPoint(PARSEC_M34.points);
      g.append('circle')
        .attr('cx', x(pTurnoff.bv))
        .attr('cy', y(pTurnoff.mv))
        .attr('r', 4)
        .attr('fill', 'none')
        .attr('stroke', PARSEC_COLOR)
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '3 2');
      g.append('text')
        .attr('x', x(pTurnoff.bv) + 10)
        .attr('y', y(pTurnoff.mv) - 6)
        .attr('font-family', 'Libre Franklin, sans-serif')
        .attr('font-size', 9)
        .attr('fill', PARSEC_COLOR)
        .text('PARSEC turnoff');
    }

    if (mode === 'binary') {
      drawIso(primaryIso, '#e8c547', 2.5);
      const binaryTrack = primaryIso.map((p) => ({ mv: p.mv - 0.75, bv: p.bv }));
      drawIso(binaryTrack, '#9ec5ff', 1.5, '6 4', 0.85);

      g.append('text')
        .attr('x', x(0.35))
        .attr('y', y(3.5))
        .attr('font-family', 'Libre Franklin, sans-serif')
        .attr('font-size', 9)
        .attr('fill', '#9ec5ff')
        .text('equal-mass binary track');
    }

    const hasExcelFlags = stars.some((s) => s.excelBinary || s.excelSingle);
    const filtered =
      highlight === 'all'
        ? stars
        : highlight === 'binary'
          ? hasExcelFlags
            ? stars.filter((s) => s.excelBinary)
            : stars.filter((_, i) => i % 5 === 0)
          : hasExcelFlags
            ? stars.filter((s) => s.excelSingle)
            : stars.filter((_, i) => i % 5 !== 0);

    const tip = tooltipRef.current!;

    g.selectAll('circle')
      .data(filtered)
      .join('circle')
      .attr('cx', (d) => x(d.bv))
      .attr('cy', (d) => y(d.mv))
      .attr('r', 3)
      .attr('fill', (d) => (d.excelBinary ? '#d4a72c' : d.cgMember === false ? '#666' : '#f0f0f0'))
      .attr('opacity', (d) => (d.cgMember === false ? 0.2 : 0.45))
      .on('mouseenter', (event, d) => {
        d3.select(event.currentTarget as SVGCircleElement).attr('opacity', 1).attr('r', 5);
        tip.style.opacity = '1';
        const lines = [
          `V = ${d.v.toFixed(2)} · B−V = ${d.bv.toFixed(2)}`,
          `Mv = ${d.mv.toFixed(2)}`,
        ];
        if (d.cgProba != null) lines.push(`P(member) = ${d.cgProba.toFixed(2)}`);
        if (d.excelBinary) lines.push('Excel binary candidate');
        if (d.excelSingle) lines.push('Excel single-star accept');
        tip.innerHTML = lines.join('<br/>');
        tip.style.left = `${event.offsetX + 12}px`;
        tip.style.top = `${event.offsetY - 8}px`;
      })
      .on('mouseleave', (event) => {
        d3.select(event.currentTarget as SVGCircleElement).attr('opacity', 0.45).attr('r', 3);
        tip.style.opacity = '0';
      });

    if (showAgeCompare && compareSet.length) {
      const legendX = width - margin.right - 4;
      let legendY = margin.top + 8;
      compareSet.forEach((ageIso) => {
        const color = AGE_COLORS[ageIso.ageGyr] ?? '#888';
        g.append('line')
          .attr('x1', legendX - 36)
          .attr('x2', legendX - 14)
          .attr('y1', legendY)
          .attr('y2', legendY)
          .attr('stroke', color)
          .attr('stroke-width', ageIso.ageGyr === 0.2 && mode === 'age-fit' ? 2.5 : 1.5);
        g.append('text')
          .attr('x', legendX - 10)
          .attr('y', legendY + 3)
          .attr('font-family', 'Libre Franklin, sans-serif')
          .attr('font-size', 9)
          .attr('fill', '#9aa8c4')
          .text(ageIso.shortLabel);
        legendY += 16;
      });
      g.append('line')
        .attr('x1', legendX - 36)
        .attr('x2', legendX - 14)
        .attr('y1', legendY)
        .attr('y2', legendY)
        .attr('stroke', PARSEC_COLOR)
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '4 3');
      g.append('text')
        .attr('x', legendX - 10)
        .attr('y', legendY + 3)
        .attr('font-family', 'Libre Franklin, sans-serif')
        .attr('font-size', 9)
        .attr('fill', '#9aa8c4')
        .text('PARSEC');
    }

    if (mode === 'binary') {
      const legendX = width - margin.right - 4;
      let legendY = margin.top + 8;
      [
        { color: '#e8c547', label: 'single-star isochrone', dash: '' },
        { color: '#9ec5ff', label: 'binary track (ΔMv ≈ 0.75)', dash: '4 3' },
      ].forEach(({ color, label, dash }) => {
        g.append('line')
          .attr('x1', legendX - 36)
          .attr('x2', legendX - 14)
          .attr('y1', legendY)
          .attr('y2', legendY)
          .attr('stroke', color)
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', dash || null);
        g.append('text')
          .attr('x', legendX - 10)
          .attr('y', legendY + 3)
          .attr('font-family', 'Libre Franklin, sans-serif')
          .attr('font-size', 8)
          .attr('fill', '#9aa8c4')
          .text(label);
        legendY += 16;
      });
    }
  }, [stars, isochrone, ageIsochrones, compareAges, mode, highlight]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} className="chart-svg" role="img" aria-label="Hertzsprung-Russell diagram" />
      <div ref={tooltipRef} className="chart-tooltip" />
    </div>
  );
}
