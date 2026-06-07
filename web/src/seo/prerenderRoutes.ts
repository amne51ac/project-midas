import { CONTINUED_SECTIONS, HOME_SECTION_IDS, routeToPath, type AppRoute } from '../routing/appRoute';

export function getAllRoutes(): AppRoute[] {
  const routes: AppRoute[] = [{ type: 'home' }];

  for (const section of HOME_SECTION_IDS) {
    routes.push({ type: 'home', section });
  }

  routes.push({ type: 'continued' });
  for (const { id } of CONTINUED_SECTIONS) {
    routes.push({ type: 'continued', section: id });
  }

  routes.push({ type: 'credence' });
  routes.push({ type: 'atlas' });

  return routes;
}

export function canonicalUrl(route: AppRoute, siteUrl: string): string {
  const base = siteUrl.replace(/\/$/, '');
  const path = routeToPath(route);
  return path === '/' ? `${base}/` : `${base}${path}`;
}

export { routeToPath };
