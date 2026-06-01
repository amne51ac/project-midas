import { useEffect, useRef, useState } from 'react';

/** Highlight the scrolly step whose center is nearest the viewport center. */
export function useScrolly(stepCount: number) {
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const steps = containerRef.current?.querySelectorAll('[data-scrolly-step]');
    if (!steps?.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]) {
          const idx = Number((visible[0].target as HTMLElement).dataset.scrollyStep);
          if (!Number.isNaN(idx)) setActiveIndex(idx);
        }
      },
      { rootMargin: '-40% 0px -40% 0px', threshold: [0, 0.25, 0.5, 0.75, 1] },
    );

    steps.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [stepCount]);

  return { activeIndex, containerRef };
}
