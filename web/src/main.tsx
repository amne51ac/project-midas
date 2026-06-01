import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { HOME_SECTION_IDS } from './routing/appRoute';
import './styles/global.css';

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

migrateLegacyHashUrl();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
