import { useEffect, useMemo, useRef } from 'react';
import * as d3 from 'd3';
import type { AtlasBundle, AtlasCluster, AtlasStar } from '../../data/atlasTypes';

const CHART_AXIS = '#555555';
const CHART_LABEL = '#888888';
const CHART_INK = '#e8e8e8';
const CHART_INK_MUTED = '#9a9a9a';
const CHART_ACCENT = '#d4a72c';
const CHART_RULE = '#2a2a2a';

interface Props {
  stars: AtlasStar[];
  clusters: AtlasCluster[];
  activeClusters: Set<string>;
  minPBinary: number;
  meta: AtlasBundle['meta'];
}

interface ClusterStat {
  cluster: AtlasCluster;
  count: number;
  meanPBinary: number;
  binaryCandidates: number;
}

function computeClusterStats(
  stars: AtlasStar[],
  clusters: AtlasCluster[],
  activeClusters: Set<string>,
): ClusterStat[] {
  return clusters
    .filter((c) => activeClusters.has(c.id))
    .map((cluster) => {
      const subset = stars.filter((s) => s.clusterId === cluster.id);
      const count = subset.length;
      const meanPBinary = count ? d3.mean(subset, (s) => s.pBinary) ?? 0 : 0;
      const binaryCandidates = subset.filter((s) => s.pBinary >= 0.5).length;
      return { cluster, count, meanPBinary, binaryCandidates };
    })
    .sort((a, b) => b.meanPBinary - a.meanPBinary);
}

export function AtlasSciencePanel({ stars, clusters, activeClusters, minPBinary, meta }: Props) {
  const histRef = useRef<SVGSVGElement>(null);
  const scatterRef = useRef<SVGSVGElement>(null);
  const barsRef = useRef<SVGSVGElement>(null);

  const clusterStats = useMemo(
    () => computeClusterStats(stars, clusters, activeClusters),
    [stars, clusters, activeClusters],
  );

  const summary = useMemo(() => {
    const n = stars.length;
    const mean = n ? d3.mean(stars, (s) => s.pBinary) ?? 0 : 0;
    const candidates = stars.filter((s) => s.pBinary >= 0.5).length;
    const withMember = stars.filter((s) => s.pMember != null);
    const agreement =
      withMember.length > 0
        ? withMember.filter((s) => (s.pMember! >= 0.5) === (s.pBinary >= 0.5)).length /
          withMember.length
        : null;
    return { n, mean, candidates, agreement };
  }, [stars]);

  useEffect(() => {
    const svg = d3.select(histRef.current);
    if (!svg.node()) return;
    svg.selectAll('*').remove();

    const width = svg.node()!.clientWidth || 280;
    const height = 110;
    const margin = { top: 10, right: 8, bottom: 22, left: 28 };
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    if (stars.length === 0) {
      svg
        .append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', CHART_INK_MUTED)
        .attr('font-size', 10)
        .text('No stars match filters');
      return;
    }

    const bins = d3.bin().domain([0, 1]).thresholds(20)(stars.map((s) => s.pBinary));
    const x = d3
      .scaleLinear()
      .domain([0, 1])
      .range([margin.left, width - margin.right]);
    const y = d3
      .scaleLinear()
      .domain([0, d3.max(bins, (b) => b.length) ?? 1])
      .nice()
      .range([height - margin.bottom, margin.top]);

    const g = svg.append('g');

    g.selectAll('rect')
      .data(bins)
      .join('rect')
      .attr('x', (d) => x(d.x0 ?? 0) + 1)
      .attr('width', (d) => Math.max(0, x(d.x1 ?? 0) - x(d.x0 ?? 0) - 2))
      .attr('y', (d) => y(d.length))
      .attr('height', (d) => height - margin.bottom - y(d.length))
      .attr('fill', (d) => d3.interpolatePlasma(((d.x0 ?? 0) + (d.x1 ?? 0)) / 2))
      .attr('opacity', 0.85);

    g.append('line')
      .attr('x1', x(minPBinary))
      .attr('x2', x(minPBinary))
      .attr('y1', margin.top)
      .attr('y2', height - margin.bottom)
      .attr('stroke', CHART_ACCENT)
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '3 2');

    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat(d3.format('.1f')))
      .call((sel) => sel.selectAll('text').attr('fill', CHART_LABEL).attr('font-size', 9))
      .call((sel) => sel.select('.domain').attr('stroke', CHART_AXIS))
      .call((sel) => sel.selectAll('.tick line').attr('stroke', CHART_AXIS));

    g.append('text')
      .attr('x', width / 2)
      .attr('y', height - 4)
      .attr('text-anchor', 'middle')
      .attr('fill', CHART_LABEL)
      .attr('font-size', 9)
      .text('p_binary');
  }, [stars, minPBinary]);

  useEffect(() => {
    const svg = d3.select(scatterRef.current);
    if (!svg.node()) return;
    svg.selectAll('*').remove();

    const width = svg.node()!.clientWidth || 280;
    const height = 110;
    const margin = { top: 10, right: 8, bottom: 22, left: 28 };
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    if (stars.length === 0) return;

    const withMember = stars.filter((s) => s.pMember != null);
    if (withMember.length === 0) {
      svg
        .append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', CHART_INK_MUTED)
        .attr('font-size', 10)
        .text('P(member) not available');
      return;
    }

    const x = d3.scaleLinear().domain([0, 1]).range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain([0, 1]).range([height - margin.bottom, margin.top]);
    const g = svg.append('g');

    g.append('line')
      .attr('x1', x(0))
      .attr('y1', y(0))
      .attr('x2', x(1))
      .attr('y2', y(1))
      .attr('stroke', CHART_RULE)
      .attr('stroke-dasharray', '4 3')
      .attr('opacity', 0.6);

    g.selectAll('circle')
      .data(withMember)
      .join('circle')
      .attr('cx', (s) => x(s.pMember!))
      .attr('cy', (s) => y(s.pBinary))
      .attr('r', 1.6)
      .attr('fill', (s) => d3.interpolatePlasma(s.pBinary))
      .attr('fill-opacity', 0.55)
      .attr('stroke', 'none');

    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(4).tickFormat(d3.format('.1f')))
      .call((sel) => sel.selectAll('text').attr('fill', CHART_LABEL).attr('font-size', 9))
      .call((sel) => sel.select('.domain').attr('stroke', CHART_AXIS))
      .call((sel) => sel.selectAll('.tick line').attr('stroke', CHART_AXIS));

    g.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(4).tickFormat(d3.format('.1f')))
      .call((sel) => sel.selectAll('text').attr('fill', CHART_LABEL).attr('font-size', 9))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) => sel.selectAll('.tick line').attr('stroke', CHART_AXIS));

    g.append('text')
      .attr('x', width / 2)
      .attr('y', height - 4)
      .attr('text-anchor', 'middle')
      .attr('fill', CHART_LABEL)
      .attr('font-size', 9)
      .text('P(member) ingest');
  }, [stars]);

  useEffect(() => {
    const svg = d3.select(barsRef.current);
    if (!svg.node()) return;
    svg.selectAll('*').remove();

    const width = svg.node()!.clientWidth || 280;
    const height = 110;
    const margin = { top: 10, right: 12, bottom: 22, left: 72 };
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    if (clusterStats.length === 0) return;

    const y = d3
      .scaleBand()
      .domain(clusterStats.map((d) => d.cluster.id))
      .range([margin.top, height - margin.bottom])
      .padding(0.22);
    const x = d3
      .scaleLinear()
      .domain([0, 1])
      .range([margin.left, width - margin.right]);

    const g = svg.append('g');

    g.selectAll('rect')
      .data(clusterStats)
      .join('rect')
      .attr('x', margin.left)
      .attr('y', (d) => y(d.cluster.id)!)
      .attr('width', (d) => x(d.meanPBinary) - margin.left)
      .attr('height', y.bandwidth())
      .attr('fill', (d) => d3.interpolatePlasma(d.meanPBinary))
      .attr('opacity', 0.9)
      .attr('rx', 2);

    g.selectAll('text.label')
      .data(clusterStats)
      .join('text')
      .attr('class', 'label')
      .attr('x', margin.left - 6)
      .attr('y', (d) => y(d.cluster.id)! + y.bandwidth() / 2 + 3)
      .attr('text-anchor', 'end')
      .attr('fill', CHART_INK)
      .attr('font-size', 8.5)
      .text((d) => d.cluster.name.replace(/ \(.*\)/, ''));

    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(4).tickFormat(d3.format('.1f')))
      .call((sel) => sel.selectAll('text').attr('fill', CHART_LABEL).attr('font-size', 9))
      .call((sel) => sel.select('.domain').attr('stroke', CHART_AXIS))
      .call((sel) => sel.selectAll('.tick line').attr('stroke', CHART_AXIS));

    g.append('text')
      .attr('x', width / 2)
      .attr('y', height - 4)
      .attr('text-anchor', 'middle')
      .attr('fill', CHART_LABEL)
      .attr('font-size', 9)
      .text('mean p_binary by cluster');
  }, [clusterStats]);

  return (
    <section className="atlas-science-panel" aria-label="Infer summary">
      <div className="atlas-science-panel__head">
        <h2 className="atlas-science-panel__title">Infer summary</h2>
        <p className="atlas-science-panel__lede">
          Credence MLP scores for the visible sample — compare ingest membership to inferred binarity.
        </p>
      </div>

      <dl className="atlas-science-panel__stats">
        <div>
          <dt>Visible</dt>
          <dd>{summary.n.toLocaleString()}</dd>
        </div>
        <div>
          <dt>Mean p_binary</dt>
          <dd>{summary.mean.toFixed(3)}</dd>
        </div>
        <div>
          <dt>Binary candidates</dt>
          <dd>
            {summary.candidates.toLocaleString()}
            {summary.n > 0 && (
              <span className="atlas-science-panel__pct">
                {' '}
                ({((100 * summary.candidates) / summary.n).toFixed(1)}%)
              </span>
            )}
          </dd>
        </div>
        {summary.agreement != null && (
          <div>
            <dt>Ingest ↔ infer agree</dt>
            <dd>{(100 * summary.agreement).toFixed(1)}%</dd>
          </div>
        )}
        <div>
          <dt>Model</dt>
          <dd>
            {meta.modelVersion}
            {meta.holdoutF1 != null && (
              <span className="atlas-science-panel__pct"> · holdout F1 {meta.holdoutF1.toFixed(2)}</span>
            )}
          </dd>
        </div>
      </dl>

      <div className="atlas-science-panel__charts">
        <figure className="atlas-science-panel__chart">
          <figcaption>p_binary distribution</figcaption>
          <svg ref={histRef} className="atlas-science-panel__svg" role="img" aria-hidden />
        </figure>
        <figure className="atlas-science-panel__chart">
          <figcaption>Ingest vs infer</figcaption>
          <svg ref={scatterRef} className="atlas-science-panel__svg" role="img" aria-hidden />
        </figure>
        <figure className="atlas-science-panel__chart">
          <figcaption>Cluster means</figcaption>
          <svg ref={barsRef} className="atlas-science-panel__svg" role="img" aria-hidden />
        </figure>
      </div>
    </section>
  );
}
