# Project Midas

Interactive research portal for **Project Midas** — photometric search for unresolved binaries in the open cluster **M34 (NGC 1039)**.

| Directory | Purpose |
|-----------|---------|
| [`web/`](web/) | Scrollable static site (Vite + React + D3). Deployed to **GitHub Pages** and **GitLab Pages**. |
| [`research/`](research/) | Data pipelines, scripts, notebooks, and processed catalogs. |

Legacy Midas code and Excel workbooks live in the parent workspace archive (`../Midas/`, `../original_excels/`).

## Quick start — local development

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Build for production

```bash
cd web
npm run build
npm run preview   # optional local check of production build
```

### Base path (required for project Pages URLs)

Both hosts serve project sites from a subpath unless you use a custom domain:

| Host | Typical URL | `VITE_BASE_PATH` |
|------|-------------|------------------|
| GitHub Pages (custom domain) | `https://midasastronomy.com/` | `/` |
| GitHub Pages (project URL) | `https://<user>.github.io/project-midas/` | `/project-midas/` |
| GitLab Pages | `https://<group>.gitlab.io/project-midas/` | `/project-midas/` |
| Custom domain | `https://midas.example.org/` | `/` |

```bash
VITE_BASE_PATH=/project-midas/ npm run build
```

## Deployment

### GitHub Pages (production: [midasastronomy.com](https://midasastronomy.com))

1. Push this repo to GitHub.
2. **Settings → Pages → Build and deployment → Source:** GitHub Actions.
3. **Settings → Pages → Custom domain:** `midasastronomy.com` (Enforce HTTPS once DNS is verified).
4. Configure DNS at your registrar (see below).
5. Push to `main`. Workflow [`.github/workflows/pages.yml`](.github/workflows/pages.yml) builds `web/` with `VITE_BASE_PATH=/` and deploys.

The build prerenders **37 route-specific HTML shells** (home sections, phase pages, phase subnav) with unique Open Graph / canonical URLs, plus `404.html` for GitHub Pages SPA fallback. Live stats and JSON-LD are injected from `m34_sample.json` at build time. See [`web/src/seo/`](web/src/seo/).

The built site includes `CNAME` from [`web/public/CNAME`](web/public/CNAME).

#### DNS for midasastronomy.com

| Type | Name | Value |
|------|------|--------|
| `A` | `@` | `185.199.108.153` |
| `A` | `@` | `185.199.109.153` |
| `A` | `@` | `185.199.110.153` |
| `A` | `@` | `185.199.111.153` |
| `CNAME` | `www` | `amne51ac.github.io` |

Optional: add `www.midasastronomy.com` as a second custom domain in GitHub Pages and redirect apex ↔ www in registrar settings if you prefer.

Fallback URL (before DNS propagates): `https://amne51ac.github.io/project-midas/` — requires `VITE_BASE_PATH=/project-midas/`; production uses `/` for the custom domain.

### GitLab Pages

1. Push to GitLab.
2. [`.gitlab-ci.yml`](.gitlab-ci.yml) runs on the default branch and publishes `public/` (built from `web/dist`).

Pages URL: `https://<namespace>.gitlab.io/<project-name>/`

### Custom domain (either host)

1. Set `VITE_BASE_PATH=/` in CI or locally before build.
2. Configure DNS / Pages custom domain in GitHub or GitLab settings.
3. Rebuild and deploy.

## Research pipeline

See [`research/README.md`](research/README.md). Planned flow:

1. Ingest legacy Midas photometry → `research/data/raw/`
2. Cross-match Gaia DR3 via `research/scripts/`
3. Join Malofeeva / Cantat-Gaudin catalogs
4. Export summaries to `web/src/data/` for visualization

## License

Research code inherits GPL v2 from the original Midas project where applicable. Site content: project contributors.
