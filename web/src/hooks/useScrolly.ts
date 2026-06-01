import { useEffect, useRef, useState } from 'react';

/** Trailing debounce after scroll stops — eliminates jitter on mobile. */
const SETTLE_MS = 140;
/** Minimum gap between live step changes while scrolling. */
const MIN_UPDATE_MS = 100;

function isMobileLayout(): boolean {
  return window.matchMedia('(max-width: 900px)').matches;
}

/** Y coordinate in viewport: the "reading line" for picking the active step. */
function scrollyTargetY(container: HTMLElement): number {
  const header = document.querySelector('.site-header');
  const headerH = header?.getBoundingClientRect().height ?? 96;

  if (isMobileLayout()) {
    const graphic = container.querySelector('.scrolly__graphic');
    const graphicH = graphic?.getBoundingClientRect().height ?? 280;
    return headerH + graphicH + 36;
  }

  return headerH + (window.innerHeight - headerH) * 0.4;
}

function pickActiveStep(
  steps: NodeListOf<Element>,
  currentIndex: number,
  targetY: number,
): number {
  const mobile = isMobileLayout();
  const hysteresis = mobile ? 28 : 52;
  const currentEl = steps[currentIndex] as HTMLElement | undefined;

  if (currentEl) {
    const { top, bottom, height } = currentEl.getBoundingClientRect();
    const pad = Math.min(hysteresis, height * 0.2);
    if (targetY >= top - pad && targetY <= bottom + pad) {
      return currentIndex;
    }
  }

  let bestIdx = 0;
  let bestDist = Infinity;

  steps.forEach((el) => {
    const html = el as HTMLElement;
    const idx = Number(html.dataset.scrollyStep);
    if (Number.isNaN(idx)) return;

    const rect = html.getBoundingClientRect();
    const anchor = rect.top + Math.min(Math.max(rect.height * 0.25, 40), mobile ? 100 : 140);
    const dist = Math.abs(anchor - targetY);
    if (dist < bestDist) {
      bestDist = dist;
      bestIdx = idx;
    }
  });

  return bestIdx;
}

/** Highlight the scrolly step nearest the reading line; debounced to avoid flicker. */
export function useScrolly(stepCount: number) {
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef(0);
  const lastCommitRef = useRef(0);
  const rafRef = useRef(0);
  const settleTimerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    activeRef.current = 0;
    setActiveIndex(0);
  }, [stepCount]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const steps = container.querySelectorAll('[data-scrolly-step]');
    if (!steps.length) return;

    const measure = () => {
      const targetY = scrollyTargetY(container);
      return pickActiveStep(steps, activeRef.current, targetY);
    };

    const commit = (next: number, force = false) => {
      if (next === activeRef.current) return;

      const now = performance.now();
      if (!force && now - lastCommitRef.current < MIN_UPDATE_MS) return;

      activeRef.current = next;
      lastCommitRef.current = now;
      setActiveIndex(next);
    };

    const onScroll = () => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => commit(measure(), false));

      if (settleTimerRef.current) clearTimeout(settleTimerRef.current);
      settleTimerRef.current = setTimeout(() => commit(measure(), true), SETTLE_MS);
    };

    commit(measure(), true);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);

    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      cancelAnimationFrame(rafRef.current);
      if (settleTimerRef.current) clearTimeout(settleTimerRef.current);
    };
  }, [stepCount]);

  return { activeIndex, containerRef };
}
