const LINKS = [
  { href: '#history', label: 'History' },
  { href: '#sky', label: 'Sky' },
  { href: '#science', label: 'Science' },
  { href: '#data', label: 'Data' },
  { href: '#compare', label: 'Compare' },
  { href: '#code', label: 'Code' },
  { href: '#roadmap', label: 'Roadmap' },
];

export function Header() {
  return (
    <header className="site-header">
      <a className="site-header__brand" href="#">
        Project Midas
      </a>
      <nav className="site-header__nav" aria-label="Page sections">
        {LINKS.map(({ href, label }) => (
          <a key={href} href={href}>
            {label}
          </a>
        ))}
      </nav>
    </header>
  );
}
