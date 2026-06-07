import { useEffect, useState } from 'react';
import { CREDENCE_SECTIONS } from '../data/credence';
import {
  CONTINUED_SECTIONS,
  continuedSectionHref,
  useAppRoute,
  type ContinuedSectionId,
} from '../routing/appRoute';
import { NO_SECTIONS, useScrollSpy } from '../hooks/useScrollSpy';

const HOME_SECTIONS = [
  { id: 'history', label: 'History' },
  { id: 'sky', label: 'Sky' },
  { id: 'science', label: 'Science' },
  { id: 'data', label: 'Data' },
  { id: 'compare', label: 'Compare' },
  { id: 'code', label: 'Code' },
  { id: 'credence', label: 'Credence' },
] as const;

const HOME_SECTION_IDS = HOME_SECTIONS.map(({ id }) => id);
const CONTINUED_SECTION_IDS = CONTINUED_SECTIONS.map(({ id }) => id);
const CREDENCE_SECTION_IDS = CREDENCE_SECTIONS.map(({ id }) => id);

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
  const route = useAppRoute();
  const [menuOpen, setMenuOpen] = useState(false);
  const isHome = route.type === 'home';
  const isContinued = route.type === 'continued';
  const isCredence = route.type === 'credence';
  const isAtlas = route.type === 'atlas';

  useEffect(() => {
    document.documentElement.classList.toggle('is-home-route', isHome);
    document.documentElement.classList.toggle('is-continued-route', isContinued);
    document.documentElement.classList.toggle('is-credence-route', isCredence);
    return () => {
      document.documentElement.classList.remove('is-home-route');
      document.documentElement.classList.remove('is-continued-route');
      document.documentElement.classList.remove('is-credence-route');
    };
  }, [isHome, isContinued, isCredence]);

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

  const homeActiveSection = useScrollSpy(isHome ? HOME_SECTION_IDS : NO_SECTIONS, {
    initialId: route.type === 'home' ? route.section : undefined,
  });

  const continuedActiveSection = useScrollSpy(isContinued ? CONTINUED_SECTION_IDS : NO_SECTIONS, {
    initialId: route.type === 'continued' ? route.section : undefined,
  });

  const credenceActiveSection = useScrollSpy(isCredence ? CREDENCE_SECTION_IDS : NO_SECTIONS, {
    initialId: undefined,
  });

  const isSectionActive = (id: string) => isHome && homeActiveSection === id;
  const isContinuedSectionActive = (id: ContinuedSectionId) =>
    isContinued && continuedActiveSection === id;
  const isCredenceSectionActive = (id: string) => isCredence && credenceActiveSection === id;

  const hasSubnav = isHome || isContinued || isCredence;

  return (
    <header className={`site-header${hasSubnav ? ' site-header--home' : ''}`}>
      <div className="site-header__bar">
        <a className="site-header__brand" href="/" onClick={closeMenu}>
          Project Midas
        </a>

        <nav className="site-header__primary" aria-label="Site sections">
          <a
            href="/"
            className={navLinkClass(isHome)}
            aria-current={isHome ? 'page' : undefined}
            onClick={closeMenu}
          >
            Home
          </a>
          <a
            href="/continued"
            className={navLinkClass(isContinued)}
            aria-current={isContinued ? 'page' : undefined}
            onClick={closeMenu}
          >
            Midas Continued
          </a>
          <a
            href="/credence"
            className={navLinkClass(isCredence)}
            aria-current={isCredence ? 'page' : undefined}
            onClick={closeMenu}
          >
            Credence
          </a>
          <a
            href="/atlas"
            className={navLinkClass(isAtlas)}
            aria-current={isAtlas ? 'page' : undefined}
            onClick={closeMenu}
          >
            Atlas
          </a>
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
              href={`/${id}`}
              className={navLinkClass(isSectionActive(id))}
              aria-current={isSectionActive(id) ? 'location' : undefined}
              onClick={closeMenu}
            >
              {label}
            </a>
          ))}
        </nav>
      )}

      {isContinued && (
        <nav className="site-header__subnav" aria-label="Continued sections">
          {CONTINUED_SECTIONS.map(({ id, label }) => (
            <a
              key={id}
              href={continuedSectionHref(id)}
              className={navLinkClass(isContinuedSectionActive(id))}
              aria-current={isContinuedSectionActive(id) ? 'location' : undefined}
              onClick={closeMenu}
            >
              {label}
            </a>
          ))}
        </nav>
      )}

      {isCredence && (
        <nav className="site-header__subnav" aria-label="Credence sections">
          {CREDENCE_SECTIONS.map(({ id, label }) => (
            <a
              key={id}
              href={`/credence#${id}`}
              className={navLinkClass(isCredenceSectionActive(id))}
              aria-current={isCredenceSectionActive(id) ? 'location' : undefined}
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
        <p className="site-header__drawer-label">Site</p>
        <a href="/" className={navLinkClass(isHome)} onClick={closeMenu}>
          Home
        </a>
        <a href="/continued" className={navLinkClass(isContinued)} onClick={closeMenu}>
          Midas Continued
        </a>
        <a href="/atlas" className={navLinkClass(isAtlas)} onClick={closeMenu}>
          Atlas
        </a>
        <a href="/credence" className={navLinkClass(isCredence)} onClick={closeMenu}>
          Credence
        </a>
        {isHome && (
          <>
            <p className="site-header__drawer-label">Sections</p>
            {HOME_SECTIONS.map(({ id, label }) => (
              <a
                key={id}
                href={`/${id}`}
                className={navLinkClass(isSectionActive(id))}
                onClick={closeMenu}
              >
                {label}
              </a>
            ))}
          </>
        )}
        {isContinued && (
          <>
            <p className="site-header__drawer-label">On this page</p>
            {CONTINUED_SECTIONS.map(({ id, label }) => (
              <a
                key={id}
                href={continuedSectionHref(id)}
                className={navLinkClass(isContinuedSectionActive(id))}
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
