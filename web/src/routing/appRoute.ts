import { useEffect, useState } from 'react';

export const CONTINUED_SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'phase-i', label: 'Phase I' },
  { id: 'phase-ii', label: 'Phase II' },
  { id: 'phase-iii', label: 'Phase III' },
  { id: 'phase-iv', label: 'Phase IV' },
  { id: 'findings', label: 'Findings' },
  { id: 'tools', label: 'Tools' },
  { id: 'questions', label: 'Questions' },
] as const;

export type ContinuedSectionId = (typeof CONTINUED_SECTIONS)[number]['id'];

export const HOME_SECTION_IDS = [
  'history',
  'sky',
  'science',
  'data',
  'compare',
  'code',
  'credence',
] as const;

export type HomeSectionId = (typeof HOME_SECTION_IDS)[number];

export type AppRoute =
  | { type: 'home'; section?: HomeSectionId }
  | { type: 'continued'; section?: ContinuedSectionId }
  | { type: 'credence' }
  | { type: 'atlas' };

function isHomeSection(value: string): value is HomeSectionId {
  return (HOME_SECTION_IDS as readonly string[]).includes(value);
}

function isContinuedSection(value: string): value is ContinuedSectionId {
  return (CONTINUED_SECTIONS as readonly { id: string }[]).some((s) => s.id === value);
}

const LEGACY_PHASE_IDS = ['phase-i', 'phase-ii', 'phase-iii', 'phase-iv'] as const;

function legacyPhaseToContinued(path: string): AppRoute | null {
  if (path === '/findings') return { type: 'continued', section: 'findings' };

  if (path.startsWith('/phases/')) {
    const phaseId = path.slice('/phases/'.length).split('/').filter(Boolean)[0];
    if (phaseId && (LEGACY_PHASE_IDS as readonly string[]).includes(phaseId)) {
      return { type: 'continued', section: phaseId as ContinuedSectionId };
    }
  }

  if (path === '/tools' || path === '/roadmap') return { type: 'continued', section: 'tools' };

  return null;
}

export function parsePathname(pathname: string): AppRoute {
  const path = pathname.replace(/\/+$/, '') || '/';

  if (path === '/') return { type: 'home' };

  if (path === '/credence') return { type: 'credence' };

  if (path === '/atlas') return { type: 'atlas' };

  const legacy = legacyPhaseToContinued(path);
  if (legacy) return legacy;

  if (path === '/continued') return { type: 'continued' };

  if (path.startsWith('/continued/')) {
    const sectionRaw = path.slice('/continued/'.length).split('/').filter(Boolean)[0];
    if (sectionRaw && isContinuedSection(sectionRaw)) {
      return { type: 'continued', section: sectionRaw };
    }
    return { type: 'continued' };
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
  if (route.type === 'credence') return '/credence';
  if (route.type === 'atlas') return '/atlas';
  if (route.type === 'continued') {
    return route.section ? `/continued/${route.section}` : '/continued';
  }
  if (route.type === 'home') {
    return route.section ? `/${route.section}` : '/';
  }
  return '/';
}

export function routeToFilePath(route: AppRoute): string {
  if (route.type === 'credence') return 'credence/index.html';
  if (route.type === 'atlas') return 'atlas/index.html';
  if (route.type === 'continued') {
    return route.section ? `continued/${route.section}/index.html` : 'continued/index.html';
  }
  if (route.type === 'home') {
    return route.section ? `${route.section}/index.html` : 'index.html';
  }
  return 'index.html';
}

export function continuedSectionHref(sectionId?: ContinuedSectionId): string {
  return sectionId ? `/continued/${sectionId}` : '/continued';
}

export function homeSectionHref(sectionId: string): string {
  return `/${sectionId}`;
}

/** @deprecated Use continuedSectionHref */
export function phasePageHref(phaseId: string): string {
  return continuedSectionHref(phaseId as ContinuedSectionId);
}

/** @deprecated Use useAppRoute */
export const useHashRoute = useAppRoute;
