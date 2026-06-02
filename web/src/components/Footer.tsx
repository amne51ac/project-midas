import { SITE } from '../seo/buildSeo';

export function Footer() {
  return (
    <footer className="site-footer">
      <div>
        <strong>Project Midas</strong> · Open cluster M34 (NGC 1039)
      </div>
      <div>
        <a href={SITE.github} rel="noopener noreferrer">
          GitHub
        </a>
      </div>
    </footer>
  );
}
