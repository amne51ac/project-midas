import { useEffect, useState } from 'react';

export const PHASE_SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'writeup', label: 'What we did' },
  { id: 'tracker', label: 'Task tracker' },
  { id: 'explorations', label: 'Explorations' },
] as const;

export type PhaseSectionId = (typeof PHASE_SECTIONS)[number]['id'];

export type AppRoute =
  | { type: 'home'; section?: string }
  | { type: 'phase'; phaseId: string; section?: PhaseSectionId };

function parseHash(): AppRoute {
  const raw = window.location.hash.replace(/^#/, '').trim();
  if (raw.startsWith('/phases/')) {
    const parts = raw.slice('/phases/'.length).split('/').filter(Boolean);
    const phaseId = parts[0];
    const section = parts[1] as PhaseSectionId | undefined;
    if (phaseId) return { type: 'phase', phaseId, section };
  }
  if (raw === '' || raw === '/') return { type: 'home' };
  if (raw.startsWith('/')) return { type: 'home' };
  return { type: 'home', section: raw };
}

export function useHashRoute(): AppRoute {
  const [route, setRoute] = useState<AppRoute>(parseHash);

  useEffect(() => {
    const onHashChange = () => setRoute(parseHash());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  return route;
}

export function phasePageHref(phaseId: string, sectionId?: PhaseSectionId): string {
  return sectionId ? `#/phases/${phaseId}/${sectionId}` : `#/phases/${phaseId}`;
}

export function homeSectionHref(sectionId: string): string {
  return `#${sectionId}`;
}
