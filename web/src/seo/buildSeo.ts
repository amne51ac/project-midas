import sampleBundle from '../data/m34_sample.json';
import catalogBundle from '../data/m34_catalogs.json';
import { ROADMAP_PHASES, overallProgress, type RoadmapPhase } from '../data/roadmap';
import type { AppRoute } from '../routing/appRoute';
import { canonicalUrl, getAllRoutes, routeToPath } from './prerenderRoutes';

export const SITE = {
  name: 'Project Midas',
  url: 'https://midasastronomy.com',
  locale: 'en_US',
  themeColor: '#070b14',
  github: 'https://github.com/amne51ac/project-midas',
  defaultTitle: 'Project Midas · M34 (NGC 1039)',
  ogImagePath: '/images/m34-hero.jpg',
  ogImageAlt: 'Open star cluster Messier 34 (NGC 1039) in Perseus',
  twitterCard: 'summary_large_image' as const,
} as const;

export interface SiteStats {
  nMidas: number;
  nSample: number;
  nGaiaMatched: number;
  nCgMembers: number;
  distancePc: number;
  ebv: number;
  catalogLayers: number;
  gaiaFieldCount: number;
  phasesComplete: number;
  phasesTotal: number;
  progressPct: number;
  currentPhase: string;
}

export interface PageMeta {
  title: string;
  description: string;
  ogImagePath?: string;
  ogImageAlt?: string;
}

const HOME_SECTIONS: Record<string, PageMeta> = {
  history: {
    title: 'History · Project Midas',
    description: 'Timeline of the Midas photometric survey and the revival effort for M34 (NGC 1039).',
  },
  sky: {
    title: 'Sky · M34 finder chart',
    description:
      'Locate Messier 34 in Perseus — finder chart, DSS imagery, and cluster context at ~470 pc.',
  },
  science: {
    title: 'Science · HR diagram & isochrones',
    description:
      'Interactive Hertzsprung–Russell diagram for M34: Yonsei–Yale and PARSEC isochrones, age ~200 Myr, binary track offsets.',
  },
  data: {
    title: 'Data · Multi-catalog explorer',
    description:
      'Compare Midas BVR, Gaia DR3, Cantat-Gaudin, Malofeeva IR, WOCS, and Jones–Prosser on one sky map.',
  },
  compare: {
    title: 'Compare · Catalog footprints',
    description:
      'Catalog sizes and Midas join-table overlap — Gaia, membership, Malofeeva, WOCS, Excel binary flags.',
  },
  code: {
    title: 'Code · Interactive demos',
    description: 'In-browser Python (Pyodide) demos for distance modulus, Q-values, and pipeline arithmetic.',
  },
  tools: {
    title: 'Tools · Pipeline inventory',
    description: 'Scripts, notebooks, and external archives used in the Project Midas revival.',
  },
  roadmap: {
    title: 'Roadmap · Project phases',
    description: 'Four-phase plan: legacy ingest, Gaia integration, validation, and synthesis.',
  },
};

export function getSiteStats(): SiteStats {
  const meta = sampleBundle.meta;
  const gaiaLayer = catalogBundle.layers.find((l) => l.id === 'gaia_field');
  const complete = ROADMAP_PHASES.filter((p) => p.status === 'complete');
  const active = ROADMAP_PHASES.find((p) => p.status === 'active');
  const upcoming = ROADMAP_PHASES.find((p) => p.status === 'upcoming');

  return {
    nMidas: meta.n_total,
    nSample: meta.n_sample,
    nGaiaMatched: meta.n_gaia_matched,
    nCgMembers: meta.n_cg_members,
    distancePc: meta.distance_pc,
    ebv: meta.ebv,
    catalogLayers: catalogBundle.layers.length,
    gaiaFieldCount: gaiaLayer?.totalCount ?? 15211,
    phasesComplete: complete.length,
    phasesTotal: ROADMAP_PHASES.length,
    progressPct: overallProgress(ROADMAP_PHASES),
    currentPhase: active?.label ?? upcoming?.label ?? complete[complete.length - 1]?.label ?? 'Phase IV',
  };
}

export function buildDefaultDescription(stats = getSiteStats()): string {
  return (
    `Project Midas — photometric search for unresolved binaries in M34 (NGC 1039). ` +
    `${stats.nMidas.toLocaleString()} legacy BVR stars, ${stats.nGaiaMatched.toLocaleString()} Gaia DR3 matches, ` +
    `${stats.nCgMembers} high-confidence members, ${stats.catalogLayers}-catalog explorer. ` +
    `${stats.phasesComplete}/${stats.phasesTotal} research phases complete (${stats.progressPct}%). ` +
    `Interactive HR diagrams, isochrone gallery, Q-value validation, open pipelines.`
  );
}

export function buildKeywords(stats = getSiteStats()): string {
  return [
    'M34',
    'NGC 1039',
    'Messier 34',
    'open cluster',
    'binary stars',
    'unresolved binaries',
    'Hertzsprung-Russell diagram',
    'isochrone fitting',
    'Gaia DR3',
    'BVR photometry',
    'Project Midas',
    'stellar astronomy',
    'Cantat-Gaudin',
    'WOCS',
    `distance ${stats.distancePc} pc`,
  ].join(', ');
}

export function absoluteUrl(path: string): string {
  const base = SITE.url.replace(/\/$/, '');
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalized}`;
}

function phaseDescription(phase: RoadmapPhase): string {
  const done = phase.tasks.filter((t) => t.status === 'done').length;
  const stats = phase.explorations
    .map((e) => e.stat)
    .filter(Boolean)
    .slice(0, 2)
    .join(' · ');
  const taskLine = `${done}/${phase.tasks.length} tasks complete`;
  return stats ? `${phase.summary} ${taskLine}. ${stats}.` : `${phase.summary} ${taskLine}.`;
}

export function getPageMeta(route: AppRoute): PageMeta {
  if (route.type === 'findings') {
    const stats = getSiteStats();
    return {
      title: 'Findings · Project Midas',
      description:
        `Synthesis of the M34 revival: ${stats.nCgMembers} Cantat-Gaudin members, ` +
        '96% union binary fraction, Q vs Malofeeva channel overlap, W2−BP method comparison, ' +
        'Rubin white dwarf check, and reproduction pipeline.',
    };
  }

  if (route.type === 'credence') {
    return {
      title: 'Credence · Project Midas',
      description:
        'Credence — ingest, resolve, infer, and display open-cluster stars in a planetarium atlas. ' +
        'M34 infer F1 ≈ 0.66 vs legacy Q ≈ 0.55. Galaxy-scale tiers from Cantat-Gaudin and Hunt catalogs.',
    };
  }

  if (route.type === 'phase') {
    const phase = ROADMAP_PHASES.find((p) => p.id === route.phaseId);
    if (phase) {
      const sectionLabel =
        route.section &&
        ({ overview: 'Overview', writeup: 'What we did', tracker: 'Task tracker', explorations: 'Explorations' } as const)[
          route.section
        ];
      return {
        title: sectionLabel
          ? `${phase.label}: ${sectionLabel} · Project Midas`
          : `${phase.label}: ${phase.title} · Project Midas`,
        description: phaseDescription(phase),
      };
    }
  }

  if (route.type === 'home' && route.section && HOME_SECTIONS[route.section]) {
    return HOME_SECTIONS[route.section];
  }

  return {
    title: SITE.defaultTitle,
    description: buildDefaultDescription(),
    ogImagePath: SITE.ogImagePath,
    ogImageAlt: SITE.ogImageAlt,
  };
}

export function buildJsonLd(stats = getSiteStats()): object[] {
  const description = buildDefaultDescription(stats);

  return [
    {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: SITE.name,
      url: SITE.url,
      description,
      inLanguage: 'en',
      about: {
        '@type': 'CelestialBody',
        name: 'Messier 34',
        alternateName: ['NGC 1039', 'M34'],
        description: `Open star cluster in Perseus at ~${stats.distancePc} pc`,
      },
      publisher: {
        '@type': 'Organization',
        name: SITE.name,
        url: SITE.url,
      },
      sameAs: [SITE.github],
    },
    {
      '@context': 'https://schema.org',
      '@type': 'ResearchProject',
      name: 'Project Midas revival — M34 binary census',
      url: SITE.url,
      description,
      keywords: buildKeywords(stats),
      sourceOrganization: { '@type': 'Organization', name: SITE.name },
      funding: 'Community / open research revival of legacy Midas photometry',
    },
    {
      '@context': 'https://schema.org',
      '@type': 'Dataset',
      name: 'Project Midas M34 join sample',
      description: `Midas BVR photometry cross-matched to Gaia DR3 and ancillary catalogs for NGC 1039.`,
      url: SITE.github,
      license: 'https://www.gnu.org/licenses/gpl-2.0.html',
      creator: { '@type': 'Organization', name: SITE.name },
      variableMeasured: ['B−V', 'V', 'Mv', 'Gaia DR3 source_id', 'membership probability'],
      distribution: {
        '@type': 'DataDownload',
        encodingFormat: 'text/csv',
        contentUrl: `${SITE.github}/blob/main/research/data/processed/m34_join.csv`,
      },
      includedInDataCatalog: {
        '@type': 'DataCatalog',
        name: 'Project Midas research data',
        url: SITE.github,
      },
      size: `${stats.nMidas} stars`,
    },
    {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: 'Project Midas roadmap',
      description: 'Four-phase research plan for reviving Midas photometry with Gaia-era validation.',
      numberOfItems: ROADMAP_PHASES.length,
      itemListElement: ROADMAP_PHASES.map((phase, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: `${phase.label}: ${phase.title}`,
        description: phase.summary,
        url: `${SITE.url}${routeToPath({ type: 'phase', phaseId: phase.id })}`,
      })),
    },
  ];
}

export function buildLlmsTxt(stats = getSiteStats()): string {
  const phaseLines = ROADMAP_PHASES.map(
    (p) =>
      `- [${p.label}: ${p.title}](${SITE.url}${routeToPath({ type: 'phase', phaseId: p.id })}) — ${p.status}; ${p.tasks.filter((t) => t.status === 'done').length}/${p.tasks.length} tasks`,
  );

  return `# ${SITE.name}

> ${buildDefaultDescription(stats)}

## Primary URL
${SITE.url}

## Repository
${SITE.github}

## Cluster
- Object: M34 / NGC 1039 (open cluster, Perseus)
- Distance: ~${stats.distancePc} pc
- Reddening: E(B−V) = ${stats.ebv}

## Data on this site
- Midas photometry: ${stats.nMidas.toLocaleString()} stars (${stats.nSample.toLocaleString()} plotted in HR sample)
- Gaia DR3 matches: ${stats.nGaiaMatched.toLocaleString()}
- Cantat-Gaudin members (P ≥ 0.7): ${stats.nCgMembers}
- Gaia field cone: ${stats.gaiaFieldCount.toLocaleString()} sources
- Catalog layers in explorer: ${stats.catalogLayers}

## Main sections
- [Findings](${SITE.url}/findings)
- [Credence](${SITE.url}/credence)
- [History](${SITE.url}/history)
- [Sky / finder chart](${SITE.url}/sky)
- [Science / HR diagram](${SITE.url}/science)
- [Data explorer](${SITE.url}/data)
- [Catalog comparison](${SITE.url}/compare)
- [Code demos](${SITE.url}/code)
- [Tools inventory](${SITE.url}/tools)
- [Roadmap](${SITE.url}/roadmap)

## Research phases
${phaseLines.join('\n')}

## Citation
Project Midas revival (${SITE.url}). M34 (NGC 1039) photometric binary census.
`;
}

export function buildSitemapXml(): string {
  const urls = getAllRoutes().map((route) => ({
    loc: canonicalUrl(route, SITE.url),
    priority:
      route.type === 'home' && !route.section
        ? '1.0'
        : route.type === 'findings'
          ? '0.9'
          : route.type === 'credence'
            ? '0.88'
            : route.type === 'phase' && !route.section
            ? '0.85'
            : route.type === 'home'
              ? '0.8'
              : '0.75',
    changefreq: route.type === 'home' && !route.section ? 'weekly' : 'monthly',
  }));

  const body = urls
    .map(
      (u) => `  <url>
    <loc>${u.loc}</loc>
    <changefreq>${u.changefreq}</changefreq>
    <priority>${u.priority}</priority>
  </url>`,
    )
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${body}
</urlset>
`;
}

export function injectSeoHtml(html: string, stats = getSiteStats()): string {
  return injectRouteHtml(html, { type: 'home' }, stats);
}

function escapeAttr(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;');
}

/** Inject route-specific title, canonical URL, and social tags into a built HTML shell. */
export function injectRouteHtml(html: string, route: AppRoute, stats = getSiteStats()): string {
  const base = injectSeoHtmlPlaceholders(html, stats);
  const meta = getPageMeta(route);
  const canonical = canonicalUrl(route, SITE.url);
  const ogImage = absoluteUrl(meta.ogImagePath ?? SITE.ogImagePath);
  const title = escapeAttr(meta.title);
  const description = escapeAttr(meta.description);
  const ogImageAlt = escapeAttr(meta.ogImageAlt ?? SITE.ogImageAlt);

  return base
    .replace(/<title>[^<]*<\/title>/, `<title>${title}</title>`)
    .replace(/<meta name="description" content="[^"]*" \/>/, `<meta name="description" content="${description}" />`)
    .replace(/<link rel="canonical" href="[^"]*" \/>/, `<link rel="canonical" href="${canonical}" />`)
    .replace(/<meta property="og:url" content="[^"]*" \/>/, `<meta property="og:url" content="${canonical}" />`)
    .replace(/<meta property="og:title" content="[^"]*" \/>/, `<meta property="og:title" content="${title}" />`)
    .replace(
      /<meta property="og:description" content="[^"]*" \/>/,
      `<meta property="og:description" content="${description}" />`,
    )
    .replace(/<meta property="og:image" content="[^"]*" \/>/, `<meta property="og:image" content="${ogImage}" />`)
    .replace(
      /<meta property="og:image:alt" content="[^"]*" \/>/,
      `<meta property="og:image:alt" content="${ogImageAlt}" />`,
    )
    .replace(/<meta name="twitter:title" content="[^"]*" \/>/, `<meta name="twitter:title" content="${title}" />`)
    .replace(
      /<meta name="twitter:description" content="[^"]*" \/>/,
      `<meta name="twitter:description" content="${description}" />`,
    )
    .replace(/<meta name="twitter:image" content="[^"]*" \/>/, `<meta name="twitter:image" content="${ogImage}" />`)
    .replace(
      /<meta name="twitter:image:alt" content="[^"]*" \/>/,
      `<meta name="twitter:image:alt" content="${ogImageAlt}" />`,
    );
}

function injectSeoHtmlPlaceholders(html: string, stats = getSiteStats()): string {
  const description = buildDefaultDescription(stats);
  const keywords = buildKeywords(stats);
  const ogImage = absoluteUrl(SITE.ogImagePath);
  const jsonLd = JSON.stringify(buildJsonLd(stats));

  return html
    .replace(/<!--seo:description-->/g, description)
    .replace(/<!--seo:keywords-->/g, keywords)
    .replace(/<!--seo:og-image-->/g, ogImage)
    .replace(/<!--seo:json-ld-->/g, jsonLd);
}
