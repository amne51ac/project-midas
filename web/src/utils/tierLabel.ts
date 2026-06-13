/** Scale tier labels (e.g. T0). Slashed zeros come from global typography. */
export function tierLabel(tier: number | string): string {
  return `T${tier}`;
}

export const T0 = tierLabel(0);
export const T1 = tierLabel(1);
export const T2 = tierLabel(2);
export const T3 = tierLabel(3);
