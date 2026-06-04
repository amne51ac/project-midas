import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { HOME_SECTION_IDS } from './routing/appRoute';
import './styles/global.css';

const LEGACY_PHASE_IDS = ['phase-i', 'phase-ii', 'phase-iii', 'phase-iv'];

/** Redirect legacy paths to the current three-page structure. */
function migrateLegacyPaths(): void {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';

  const staticRedirects: Record<string, string> = {
    '/findings': '/continued/findings',
    '/tools': '/continued/tools',
    '/roadmap': '/continued',
  };
  if (staticRedirects[path]) {
    window.location.replace(staticRedirects[path]);
    return;
  }

  if (path.startsWith('/phases/')) {
    const phaseId = path.slice('/phases/'.length).split('/').filter(Boolean)[0];
    if (phaseId && LEGACY_PHASE_IDS.includes(phaseId)) {
      window.location.replace(`/continued/${phaseId}`);
      return;
    }
  }
}

/** Redirect legacy hash routes (#/phases/…, #science) to path URLs. */
function migrateLegacyHashUrl(): void {
  const { hash } = window.location;
  if (!hash || hash === '#') return;

  if (hash.startsWith('#/')) {
    window.location.replace(hash.slice(1));
    return;
  }

  if (hash.startsWith('#demo-')) return;

  const section = hash.slice(1);
  if ((HOME_SECTION_IDS as readonly string[]).includes(section)) {
    window.location.replace(`/${section}`);
  }
}

migrateLegacyPaths();
migrateLegacyHashUrl();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
