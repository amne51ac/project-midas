import { useEffect } from 'react';
import { absoluteUrl, SITE, type PageMeta } from '../config/siteMeta';
import { canonicalUrl } from '../seo/prerenderRoutes';
import type { AppRoute } from '../routing/appRoute';

function setNamedMeta(name: string, content: string) {
  let el = document.querySelector(`meta[name="${name}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute('name', name);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function setPropertyMeta(property: string, content: string) {
  let el = document.querySelector(`meta[property="${property}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute('property', property);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function setCanonical(url: string) {
  let el = document.querySelector('link[rel="canonical"]');
  if (!el) {
    el = document.createElement('link');
    el.setAttribute('rel', 'canonical');
    document.head.appendChild(el);
  }
  el.setAttribute('href', url);
}

/** Sync document title and social meta tags when the route changes. */
export function usePageMeta(meta: PageMeta, route: AppRoute) {
  useEffect(() => {
    const ogImage = absoluteUrl(meta.ogImagePath ?? SITE.ogImagePath);
    const ogImageAlt = meta.ogImageAlt ?? SITE.ogImageAlt;
    const pageUrl = canonicalUrl(route, SITE.url);

    document.title = meta.title;
    setCanonical(pageUrl);

    setNamedMeta('description', meta.description);
    setNamedMeta('twitter:card', SITE.twitterCard);
    setNamedMeta('twitter:title', meta.title);
    setNamedMeta('twitter:description', meta.description);
    setNamedMeta('twitter:image', ogImage);
    setNamedMeta('twitter:image:alt', ogImageAlt);

    setPropertyMeta('og:title', meta.title);
    setPropertyMeta('og:description', meta.description);
    setPropertyMeta('og:type', 'website');
    setPropertyMeta('og:url', pageUrl);
    setPropertyMeta('og:site_name', SITE.name);
    setPropertyMeta('og:locale', SITE.locale);
    setPropertyMeta('og:image', ogImage);
    setPropertyMeta('og:image:alt', ogImageAlt);
  }, [meta.title, meta.description, meta.ogImagePath, meta.ogImageAlt, route]);
}
