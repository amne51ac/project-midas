import type { Plugin } from 'vite';
import { writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  buildLlmsTxt,
  buildSitemapXml,
  injectSeoHtml,
} from './src/seo/buildSeo';

const rootDir = dirname(fileURLToPath(import.meta.url));

/** Inject live pipeline stats into index.html and emit llms.txt + sitemap at build time. */
export function seoPlugin(): Plugin {
  const publicDir = resolve(rootDir, 'public');

  const writeArtifacts = () => {
    writeFileSync(resolve(publicDir, 'sitemap.xml'), buildSitemapXml(), 'utf8');
    writeFileSync(resolve(publicDir, 'llms.txt'), buildLlmsTxt(), 'utf8');
  };

  return {
    name: 'project-midas-seo',
    buildStart() {
      writeArtifacts();
    },
    transformIndexHtml(html) {
      return injectSeoHtml(html);
    },
  };
}
