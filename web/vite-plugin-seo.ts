import type { Plugin } from 'vite';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  buildLlmsTxt,
  buildSitemapXml,
  injectRouteHtml,
  injectSeoHtml,
} from './src/seo/buildSeo';
import { getAllRoutes } from './src/seo/prerenderRoutes';
import { routeToFilePath } from './src/routing/appRoute';

const rootDir = dirname(fileURLToPath(import.meta.url));

/** Inject SEO, prerender route HTML shells, and emit llms.txt + sitemap. */
export function seoPlugin(): Plugin {
  const publicDir = resolve(rootDir, 'public');

  const writePublicArtifacts = () => {
    writeFileSync(resolve(publicDir, 'sitemap.xml'), buildSitemapXml(), 'utf8');
    writeFileSync(resolve(publicDir, 'llms.txt'), buildLlmsTxt(), 'utf8');
  };

  const prerenderRoutes = (distDir: string) => {
    const shell = readFileSync(resolve(distDir, 'index.html'), 'utf8');

    for (const route of getAllRoutes()) {
      if (route.type === 'home' && !route.section) continue;

      const html = injectRouteHtml(shell, route);
      const outFile = resolve(distDir, routeToFilePath(route));
      mkdirSync(dirname(outFile), { recursive: true });
      writeFileSync(outFile, html, 'utf8');
    }

    writeFileSync(resolve(distDir, '404.html'), shell, 'utf8');
  };

  return {
    name: 'project-midas-seo',
    buildStart() {
      writePublicArtifacts();
    },
    transformIndexHtml(html) {
      return injectSeoHtml(html);
    },
    closeBundle() {
      writePublicArtifacts();
      prerenderRoutes(resolve(rootDir, 'dist'));
    },
  };
}
