import { useEffect, useState } from 'react';

export type AppRoute =
  | { type: 'home'; section?: string }
  | { type: 'phase'; phaseId: string };

function parseHash(): AppRoute {
  const raw = window.location.hash.replace(/^#/, '').trim();
  if (raw.startsWith('/phases/')) {
    const phaseId = raw.slice('/phases/'.length).split(/[/?]/)[0];
    if (phaseId) return { type: 'phase', phaseId };
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

export function phasePageHref(phaseId: string): string {
  return `#/phases/${phaseId}`;
}

export function homeSectionHref(sectionId: string): string {
  return `#${sectionId}`;
}
