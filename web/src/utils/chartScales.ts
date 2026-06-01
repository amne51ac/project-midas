/** Pad numeric axis domains so points and curves are not clipped at the edges. */

export function finiteValues(values: (number | null | undefined)[]): number[] {
  return values.filter((v): v is number => v != null && Number.isFinite(v));
}

export function extentOf(values: number[], fallback: [number, number]): [number, number] {
  if (!values.length) return fallback;
  return [Math.min(...values), Math.max(...values)];
}

export function padExtent(
  min: number,
  max: number,
  options: { fraction?: number; minPad?: number } = {},
): [number, number] {
  const { fraction = 0.08, minPad = 0 } = options;
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [min, max];
  const span = max - min || Math.abs(max) || 1;
  const pad = Math.max(span * fraction, minPad);
  return [min - pad, max + pad];
}

/** B−V vs Mv axes for HR-style plots (Mv increases upward → domain [faint, bright]). */
export function hrDomains(
  bvValues: number[],
  mvValues: number[],
  fallback: { bv?: [number, number]; mv?: [number, number] } = {},
): { xDomain: [number, number]; yDomain: [number, number] } {
  const [bvMin, bvMax] = extentOf(bvValues, fallback.bv ?? [-0.1, 1.4]);
  const [mvMin, mvMax] = extentOf(mvValues, fallback.mv ?? [2, 13]);
  const [x0, x1] = padExtent(bvMin, bvMax, { fraction: 0.06, minPad: 0.1 });
  const [mvLo, mvHi] = padExtent(mvMin, mvMax, { fraction: 0.06, minPad: 0.35 });
  return { xDomain: [x0, x1], yDomain: [mvHi, mvLo] };
}

/** Pad a [min, max] tuple — used for RA/Dec and plate-coordinate maps. */
export function padDomainTuple(
  domain: [number, number],
  options: { fraction?: number; minPad?: number } = {},
): [number, number] {
  return padExtent(domain[0], domain[1], options);
}
