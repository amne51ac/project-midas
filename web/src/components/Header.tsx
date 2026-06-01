import { useEffect, useState } from 'react';
import { phasePageHref, useHashRoute } from '../hooks/useHashRoute';

const PHASE_LINKS = [
  { phaseId: 'phase-i', label: 'Phase I' },
  { phaseId: 'phase-ii', label: 'Phase II' },
  { phaseId: 'phase-iii', label: 'Phase III' },
  { phaseId: 'phase-iv', label: 'Phase IV' },
] as const;

const HOME_SECTIONS = [
  { id: 'history', label: 'History' },
  { id: 'sky', label: 'Sky' },
  { id: 'science', label: 'Science' },
  { id: 'data', label: 'Data' },
  { id: 'compare', label: 'Compare' },
  { id: 'code', label: 'Code' },
  { id: 'tools', label: 'Tools' },
  { id: 'roadmap', label: 'Roadmap' },
] as const;

const GITHUB_URL = 'https://github.com/amne51ac/project-midas';

function GitHubIcon() {
  return (
    <svg
      className="site-header__github-icon"
      viewBox="0 0 16 16"
      width={18}
      height={18}
      aria-hidden="true"
      focusable="false"
    >
      <path
        fill="currentColor"
        d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
      />
    </svg>
  );
}

function navLinkClass(active: boolean): string {
  return active ? 'site-nav__link is-active' : 'site-nav__link';
}

export function Header() {
  const route = useHashRoute();
  const [menuOpen, setMenuOpen] = useState(false);
  const isHome = route.type === 'home';

  useEffect(() => {
    document.documentElement.classList.toggle('is-home-route', isHome);
    return () => document.documentElement.classList.remove('is-home-route');
  }, [isHome]);

  useEffect(() => {
    if (!menuOpen) return;

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenuOpen(false);
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [menuOpen]);

  const closeMenu = () => setMenuOpen(false);

  const isPhaseActive = (phaseId: string) =>
    route.type === 'phase' && route.phaseId === phaseId;

  const isSectionActive = (id: string) => route.type === 'home' && route.section === id;

  return (
    <header className={`site-header${isHome ? ' site-header--home' : ''}`}>
      <div className="site-header__bar">
        <a className="site-header__brand" href="#/" onClick={closeMenu}>
          Project Midas
        </a>

        <nav className="site-header__primary" aria-label="Project phases">
          <a
            href="#/"
            className={navLinkClass(isHome)}
            aria-current={isHome ? 'page' : undefined}
            onClick={closeMenu}
          >
            Home
          </a>
          {PHASE_LINKS.map(({ phaseId, label }) => (
            <a
              key={phaseId}
              href={phasePageHref(phaseId)}
              className={navLinkClass(isPhaseActive(phaseId))}
              aria-current={isPhaseActive(phaseId) ? 'page' : undefined}
              onClick={closeMenu}
            >
              {label}
            </a>
          ))}
        </nav>

        <div className="site-header__actions">
          <a
            className="site-header__github"
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Project Midas on GitHub"
          >
            <GitHubIcon />
          </a>
          <button
            type="button"
            className="site-header__menu-btn"
            aria-expanded={menuOpen}
            aria-controls="site-nav-drawer"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? 'Close' : 'Menu'}
          </button>
        </div>
      </div>

      {isHome && (
        <nav className="site-header__subnav" aria-label="Home sections">
          {HOME_SECTIONS.map(({ id, label }) => (
            <a
              key={id}
              href={`#${id}`}
              className={navLinkClass(isSectionActive(id))}
              aria-current={isSectionActive(id) ? 'location' : undefined}
              onClick={closeMenu}
            >
              {label}
            </a>
          ))}
        </nav>
      )}

      <div
        id="site-nav-drawer"
        className={`site-header__drawer${menuOpen ? ' is-open' : ''}`}
        aria-hidden={!menuOpen}
      >
        <p className="site-header__drawer-label">Phases</p>
        <a href="#/" className={navLinkClass(isHome)} onClick={closeMenu}>
          Home
        </a>
        {PHASE_LINKS.map(({ phaseId, label }) => (
          <a
            key={phaseId}
            href={phasePageHref(phaseId)}
            className={navLinkClass(isPhaseActive(phaseId))}
            onClick={closeMenu}
          >
            {label}
          </a>
        ))}
        {isHome && (
          <>
            <p className="site-header__drawer-label">Sections</p>
            {HOME_SECTIONS.map(({ id, label }) => (
              <a
                key={id}
                href={`#${id}`}
                className={navLinkClass(isSectionActive(id))}
                onClick={closeMenu}
              >
                {label}
              </a>
            ))}
          </>
        )}
        <p className="site-header__drawer-label">Repository</p>
        <a
          href={GITHUB_URL}
          className="site-nav__link site-nav__link--with-icon"
          target="_blank"
          rel="noopener noreferrer"
          onClick={closeMenu}
        >
          <GitHubIcon />
          GitHub
        </a>
      </div>

      {menuOpen && (
        <button
          type="button"
          className="site-header__backdrop"
          aria-label="Close menu"
          onClick={closeMenu}
        />
      )}
    </header>
  );
}
