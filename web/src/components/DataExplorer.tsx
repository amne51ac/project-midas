import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { CatalogBundle, CatalogLayer, CatalogPoint } from '../data/catalogTypes';

type ViewMode = 'sky' | 'plate';

interface Props {
  bundle: CatalogBundle;
}

function layerOpacity(id: string, active: Set<string>) {
  if (!active.has(id)) return 0;
  return id === 'midas' ? 0.7 : id === 'gaia_field' ? 0.35 : 0.85;
}

function pointRadius(layer: CatalogLayer) {
  if (layer.id === 'gaia_field') return 1.8;
  if (layer.id === 'midas') return 2.8;
  if (layer.id === 'malofeeva') return 3.4;
  if (layer.id === 'wocs') return 3.6;
  return 3.2;
}

export function DataExplorer({ bundle }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState<Set<string>>(
    () => new Set(bundle.layers.map((l) => l.id)),
  );
  const [view, setView] = useState<ViewMode>('sky');
  const [hover, setHover] = useState<{ layer: CatalogLayer; pt: CatalogPoint } | null>(null);

  const activeLayers = useMemo(
    () => bundle.layers.filter((l) => active.has(l.id)),
    [bundle.layers, active],
  );

  const canPlate = activeLayers.some((l) => l.hasPlateCoords);

  useEffect(() => {
    if (view === 'plate' && !canPlate) setView('sky');
  }, [view, canPlate]);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svg.node()) return;
    svg.selectAll('*').remove();

    const width = svgRef.current!.clientWidth || 640;
    const height = 440;
    const margin = { top: 20, right: 16, bottom: 44, left: 48 };
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const plateMode = view === 'plate';
    const midasLayer = activeLayers.find((l) => l.id === 'midas' && l.hasPlateCoords);

    let xDomain: [number, number];
    let yDomain: [number, number];

    if (plateMode && midasLayer) {
      const xs = midasLayer.points.map((p) => p.x!);
      const ys = midasLayer.points.map((p) => p.y!);
      xDomain = d3.extent(xs) as [number, number];
      yDomain = d3.extent(ys) as [number, number];
    } else {
      const all = activeLayers.flatMap((l) => l.points);
      xDomain = d3.extent(all, (p) => p.ra) as [number, number];
      yDomain = d3.extent(all, (p) => p.dec) as [number, number];
      const padRa = (xDomain[1] - xDomain[0]) * 0.04 || 0.05;
      const padDec = (yDomain[1] - yDomain[0]) * 0.04 || 0.05;
      xDomain = [xDomain[0] - padRa, xDomain[1] + padRa];
      yDomain = [yDomain[0] - padDec, yDomain[1] + padDec];
    }

    const x = d3.scaleLinear().domain(xDomain).nice().range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain(yDomain).nice().range([height - margin.bottom, margin.top]);

    const g = svg.append('g');

    // cluster footprint
    if (!plateMode) {
      g.append('circle')
        .attr('cx', x(bundle.center.ra))
        .attr('cy', y(bundle.center.dec))
        .attr('r', x(bundle.center.ra + bundle.radiusDeg) - x(bundle.center.ra))
        .attr('fill', 'none')
        .attr('stroke', '#e8c547')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '5 4')
        .attr('opacity', 0.35);
    } else {
      g.append('circle')
        .attr('cx', x(895))
        .attr('cy', y(650))
        .attr('r', 80)
        .attr('fill', 'none')
        .attr('stroke', '#e8c547')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '4 3')
        .attr('opacity', 0.4);
    }

    // draw fainter layers first
    const drawOrder = [...activeLayers].sort((a, b) => {
      const rank: Record<string, number> = {
        gaia_field: 0,
        jones_prosser: 1,
        wocs: 2,
        cantat_gaudin: 3,
        malofeeva: 4,
        midas: 5,
      };
      return (rank[a.id] ?? 1) - (rank[b.id] ?? 1);
    });

    const tip = tooltipRef.current!;

    for (const layer of drawOrder) {
      if (plateMode && layer.id !== 'midas') continue;

      const pts = layer.points.filter((p) =>
        plateMode ? p.x != null && p.y != null : true,
      );

      g.selectAll(`circle.cat-${layer.id}`)
        .data(pts)
        .join('circle')
        .attr('class', `cat-${layer.id}`)
        .attr('cx', (d) => (plateMode ? x(d.x!) : x(d.ra)))
        .attr('cy', (d) => (plateMode ? y(d.y!) : y(d.dec)))
        .attr('r', pointRadius(layer))
        .attr('fill', layer.color)
        .attr('opacity', layerOpacity(layer.id, active))
        .style('pointer-events', layerOpacity(layer.id, active) > 0 ? 'all' : 'none')
        .on('mouseenter', (event, d) => {
          d3.select(event.currentTarget as SVGCircleElement)
            .attr('r', pointRadius(layer) + 2)
            .attr('opacity', 1);
          setHover({ layer, pt: d });
          tip.style.opacity = '1';
        })
        .on('mousemove', (event) => {
          tip.style.left = `${event.offsetX + 12}px`;
          tip.style.top = `${event.offsetY - 8}px`;
        })
        .on('mouseleave', (event) => {
          d3.select(event.currentTarget as SVGCircleElement)
            .attr('r', pointRadius(layer))
            .attr('opacity', layerOpacity(layer.id, active));
          setHover(null);
          tip.style.opacity = '0';
        });
    }

    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(5))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) => sel.selectAll('text').attr('fill', '#8a98b4').attr('font-size', 10));

    g.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5))
      .call((sel) => sel.select('.domain').remove())
      .call((sel) => sel.selectAll('text').attr('fill', '#8a98b4').attr('font-size', 10));

    g.append('text')
      .attr('x', width / 2)
      .attr('y', height - 8)
      .attr('text-anchor', 'middle')
      .attr('fill', '#9aa8c4')
      .attr('font-size', 10)
      .text(plateMode ? 'Midas plate X (arcsec offset)' : 'RA (deg, J2000)');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -(height / 2))
      .attr('y', 14)
      .attr('text-anchor', 'middle')
      .attr('fill', '#9aa8c4')
      .attr('font-size', 10)
      .text(plateMode ? 'Plate Y' : 'Dec (deg)');
  }, [bundle, activeLayers, active, view]);

  const toggle = (id: string) => {
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        if (next.size > 1) next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const maxPublished = Math.max(...bundle.published.map((p) => p.totalCount), 1);

  return (
    <div className="data-explorer">
      <div className="data-explorer__controls">
        <div className="data-explorer__layers" role="group" aria-label="Catalog layers">
          {bundle.layers.map((layer) => (
            <button
              key={layer.id}
              type="button"
              className={`data-explorer__layer-btn${active.has(layer.id) ? ' is-on' : ''}`}
              aria-pressed={active.has(layer.id)}
              onClick={() => toggle(layer.id)}
            >
              <span className="data-explorer__swatch" style={{ background: layer.color }} />
              {layer.shortName}
              <span className="data-explorer__count">
                {layer.sampleCount.toLocaleString()}
                {layer.sampleCount < layer.totalCount && ` / ${layer.totalCount.toLocaleString()}`}
              </span>
            </button>
          ))}
        </div>

        <div className="data-explorer__views" role="group" aria-label="Map projection">
          <button
            type="button"
            className={`data-explorer__view-btn${view === 'sky' ? ' is-active' : ''}`}
            onClick={() => setView('sky')}
          >
            Sky (RA/Dec)
          </button>
          <button
            type="button"
            className={`data-explorer__view-btn${view === 'plate' ? ' is-active' : ''}`}
            onClick={() => setView('plate')}
            disabled={!canPlate}
            title={canPlate ? 'Midas plate coordinates' : 'Enable Midas layer for plate view'}
          >
            Midas plate
          </button>
        </div>
      </div>

      <div className="data-explorer__main">
        <div className="data-explorer__chart chart-panel">
          <svg ref={svgRef} className="chart-svg" role="img" aria-label="Multi-catalog sky map" />
          <div ref={tooltipRef} className="chart-tooltip">
            {hover && (
              <>
                <strong>{hover.layer.shortName}</strong>
                <br />
                ID {hover.pt.id}
                <br />
                RA {hover.pt.ra.toFixed(4)}° · Dec {hover.pt.dec.toFixed(4)}°
                {hover.pt.mag != null && (
                  <>
                    <br />
                    mag {hover.pt.mag.toFixed(2)}
                  </>
                )}
                {hover.pt.plx != null && (
                  <>
                    <br />
                    π {hover.pt.plx.toFixed(2)} mas
                  </>
                )}
                {hover.pt.prob != null && (
                  <>
                    <br />
                    P(member) {hover.pt.prob.toFixed(2)}
                    {hover.pt.cgMember != null && (hover.pt.cgMember ? ' · member' : ' · non-member')}
                  </>
                )}
                {hover.pt.gaiaId && (
                  <>
                    <br />
                    Gaia {hover.pt.gaiaId}
                  </>
                )}
                {hover.pt.excelBinary && (
                  <>
                    <br />
                    Excel binary
                  </>
                )}
                {hover.pt.excelSingle && (
                  <>
                    <br />
                    Excel single
                  </>
                )}
                {hover.pt.malofeeva && (
                  <>
                    <br />
                    Malofeeva IR
                  </>
                )}
                {hover.pt.wocs && (
                  <>
                    <br />
                    WOCS target
                  </>
                )}
                {hover.pt.period != null && (
                  <>
                    <br />
                    P_rot {hover.pt.period.toFixed(2)} d
                  </>
                )}
                {hover.pt.rv != null && (
                  <>
                    <br />
                    RV {hover.pt.rv.toFixed(1)} km/s
                  </>
                )}
              </>
            )}
          </div>
        </div>

        <aside className="data-explorer__aside">
          {hover ? (
            <div className="data-explorer__detail">
              <h4>{hover.layer.name}</h4>
              <p>{hover.layer.description}</p>
              <dl>
                <div>
                  <dt>ID</dt>
                  <dd>{hover.pt.id}</dd>
                </div>
                {hover.pt.mv != null && (
                  <div>
                    <dt>Mv</dt>
                    <dd>{hover.pt.mv.toFixed(2)}</dd>
                  </div>
                )}
                {hover.pt.bv != null && (
                  <div>
                    <dt>B−V</dt>
                    <dd>{hover.pt.bv.toFixed(3)}</dd>
                  </div>
                )}
                {hover.pt.mem && (
                  <div>
                    <dt>Mem code</dt>
                    <dd>{hover.pt.mem}</dd>
                  </div>
                )}
                {hover.pt.mv0 != null && (
                  <div>
                    <dt>Mv₀</dt>
                    <dd>{hover.pt.mv0.toFixed(2)}</dd>
                  </div>
                )}
                {hover.pt.bv0 != null && (
                  <div>
                    <dt>(B−V)₀</dt>
                    <dd>{hover.pt.bv0.toFixed(3)}</dd>
                  </div>
                )}
                {hover.pt.gaiaId && (
                  <div>
                    <dt>Gaia</dt>
                    <dd>{hover.pt.gaiaId}</dd>
                  </div>
                )}
                {hover.pt.prob != null && (
                  <div>
                    <dt>P(member)</dt>
                    <dd>
                      {hover.pt.prob.toFixed(3)}
                      {hover.pt.cgMember != null && (hover.pt.cgMember ? ' · member' : ' · field')}
                    </dd>
                  </div>
                )}
                {hover.pt.period != null && (
                  <div>
                    <dt>Rotation</dt>
                    <dd>{hover.pt.period.toFixed(2)} d</dd>
                  </div>
                )}
                {hover.pt.rv != null && (
                  <div>
                    <dt>Radial vel.</dt>
                    <dd>{hover.pt.rv.toFixed(1)} km/s</dd>
                  </div>
                )}
                {hover.pt.rotSeq && (
                  <div>
                    <dt>Rot. sequence</dt>
                    <dd>{hover.pt.rotSeq}</dd>
                  </div>
                )}
                {hover.pt.hw2w1 != null && (
                  <div>
                    <dt>(H−W2)−W1</dt>
                    <dd>{hover.pt.hw2w1.toFixed(2)}</dd>
                  </div>
                )}
              </dl>
            </div>
          ) : (
            <p className="data-explorer__hint">
              Toggle layers to compare catalogs on one map. Hover a point for details. Dashed circle:
              ~0.35° survey cone centered on M34.
            </p>
          )}

          {bundle.published.length > 0 && (
            <>
              <h4 className="data-explorer__aside-heading">Related archives</h4>
              <ul className="data-explorer__published">
                {bundle.published.map((pub) => (
                  <li key={pub.id}>
                    <div className="data-explorer__pub-row">
                      <span>{pub.name}</span>
                      <span>{pub.totalCount.toLocaleString()}</span>
                    </div>
                    <div className="data-explorer__pub-bar-wrap">
                      <div
                        className="data-explorer__pub-bar"
                        style={{ width: `${(pub.totalCount / maxPublished) * 100}%` }}
                      />
                    </div>
                    <p className="data-explorer__pub-note">{pub.note}</p>
                  </li>
                ))}
              </ul>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
