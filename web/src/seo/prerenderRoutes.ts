import { ROADMAP_PHASES } from '../data/roadmap';
import {
  HOME_SECTION_IDS,
  PHASE_SECTIONS,
  routeToPath,
  type AppRoute,
} from '../routing/appRoute';

export function getAllRoutes(): AppRoute[] {
  const routes: AppRoute[] = [{ type: 'home' }];

  for (const section of HOME_SECTION_IDS) {
    routes.push({ type: 'home', section });
  }

  for (const phase of ROADMAP_PHASES) {
    routes.push({ type: 'phase', phaseId: phase.id });
    for (const { id } of PHASE_SECTIONS) {
      routes.push({ type: 'phase', phaseId: phase.id, section: id });
    }
  }

  return routes;
}

export function canonicalUrl(route: AppRoute, siteUrl: string): string {
  const base = siteUrl.replace(/\/$/, '');
  const path = routeToPath(route);
  return path === '/' ? `${base}/` : `${base}${path}`;
}

export { routeToPath };
