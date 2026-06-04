import { useEffect, useState } from 'react';

export const PHASE_SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'writeup', label: 'What we did' },
  { id: 'tracker', label: 'Task tracker' },
  { id: 'explorations', label: 'Explorations' },
] as const;

export type PhaseSectionId = (typeof PHASE_SECTIONS)[number]['id'];

export const HOME_SECTION_IDS = [
  'history',
  'sky',
  'science',
  'data',
  'compare',
  'code',
  'tools',
  'roadmap',
] as const;

export type HomeSectionId = (typeof HOME_SECTION_IDS)[number];

export type AppRoute =
  | { type: 'home'; section?: HomeSectionId }
  | { type: 'phase'; phaseId: string; section?: PhaseSectionId }
  | { type: 'findings' }
  | { type: 'prism' };

function isHomeSection(value: string): value is HomeSectionId {
  return (HOME_SECTION_IDS as readonly string[]).includes(value);
}

function isPhaseSection(value: string): value is PhaseSectionId {
  return (PHASE_SECTIONS as readonly { id: string }[]).some((s) => s.id === value);
}

export function parsePathname(pathname: string): AppRoute {
  const path = pathname.replace(/\/+$/, '') || '/';

  if (path === '/') return { type: 'home' };

  if (path === '/findings') return { type: 'findings' };

  if (path === '/prism') return { type: 'prism' };

  if (path.startsWith('/phases/')) {
    const parts = path.slice('/phases/'.length).split('/').filter(Boolean);
    const phaseId = parts[0];
    const sectionRaw = parts[1];
    if (phaseId) {
      return {
        type: 'phase',
        phaseId,
        section: sectionRaw && isPhaseSection(sectionRaw) ? sectionRaw : undefined,
      };
    }
  }

  const section = path.slice(1);
  if (isHomeSection(section)) return { type: 'home', section };

  return { type: 'home' };
}

export function useAppRoute(): AppRoute {
  const [route, setRoute] = useState<AppRoute>(() => parsePathname(window.location.pathname));

  useEffect(() => {
    const onNavigate = () => setRoute(parsePathname(window.location.pathname));
    window.addEventListener('popstate', onNavigate);
    return () => window.removeEventListener('popstate', onNavigate);
  }, []);

  return route;
}

export function routeToPath(route: AppRoute): string {
  if (route.type === 'findings') return '/findings';
  if (route.type === 'prism') return '/prism';
  if (route.type === 'home') {
    return route.section ? `/${route.section}` : '/';
  }
  return route.section
    ? `/phases/${route.phaseId}/${route.section}`
    : `/phases/${route.phaseId}`;
}

export function routeToFilePath(route: AppRoute): string {
  if (route.type === 'findings') return 'findings/index.html';
  if (route.type === 'prism') return 'prism/index.html';
  if (route.type === 'home') {
    return route.section ? `${route.section}/index.html` : 'index.html';
  }
  return route.section
    ? `phases/${route.phaseId}/${route.section}/index.html`
    : `phases/${route.phaseId}/index.html`;
}

export function phasePageHref(phaseId: string, sectionId?: PhaseSectionId): string {
  return sectionId ? `/phases/${phaseId}/${sectionId}` : `/phases/${phaseId}`;
}

export function homeSectionHref(sectionId: string): string {
  return `/${sectionId}`;
}

/** @deprecated Use useAppRoute */
export const useHashRoute = useAppRoute;
