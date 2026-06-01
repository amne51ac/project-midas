import { useEffect, useState } from 'react';

const NO_SECTIONS: readonly string[] = [];

function headerOffset(): number {
  const header = document.querySelector('.site-header');
  return (header?.getBoundingClientRect().height ?? 120) + 8;
}

function resolveActiveSection(
  sectionIds: readonly string[],
  elementId: (id: string) => string,
): string | undefined {
  if (!sectionIds.length) return undefined;

  const offset = headerOffset();
  let current = sectionIds[0];

  for (const id of sectionIds) {
    const el = document.getElementById(elementId(id));
    if (!el) continue;
    if (el.getBoundingClientRect().top <= offset) {
      current = id;
    }
  }

  return current;
}

interface ScrollSpyOptions {
  /** Prefix for DOM ids, e.g. `phase-` → `phase-overview`. */
  elementPrefix?: string;
  /** Jump to this section when the hash changes before scroll settles. */
  initialId?: string;
}

export function useScrollSpy(
  sectionIds: readonly string[],
  options: ScrollSpyOptions = {},
): string | undefined {
  const { elementPrefix = '', initialId } = options;
  const elementId = (id: string) => `${elementPrefix}${id}`;

  const [activeId, setActiveId] = useState<string | undefined>(
    () => initialId ?? sectionIds[0],
  );

  useEffect(() => {
    if (initialId) setActiveId(initialId);
  }, [initialId]);

  useEffect(() => {
    if (!sectionIds.length) return;

    let frame = 0;

    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const next = resolveActiveSection(sectionIds, elementId);
        if (next) setActiveId((prev) => (prev === next ? prev : next));
      });
    };

    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('scroll', update);
      window.removeEventListener('resize', update);
    };
  }, [sectionIds]);

  return activeId;
}

export { NO_SECTIONS };
