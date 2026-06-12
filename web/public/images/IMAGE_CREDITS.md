# Sky image credits (M34 field)

Images in `web/public/images/` used on the site.

| File | Source | License / terms |
|------|--------|-----------------|
| `all-sky-milkyway.jpg` | [NASA SVS Tycho Catalog Skymap](https://svs.gsfc.nasa.gov/3442/) (`TychoSkymap.t5_04096x02048.jpg`, 4096×2048) | Public domain — credit **NASA/GSFC Scientific Visualization Studio** (Tom Bridgman). Celestial plate carrée in equatorial coordinates for alignment with RA/Dec overlays. |

| File | Source | License / terms |
|------|--------|-----------------|
| `m34-noirlab-1996.jpg` | [NOIRLab noao-m34](https://noirlab.edu/public/images/noao-m34/) (screen) | Credit required: REU program / NOIRLab / NSF / AURA |
| `m34-hero.jpg` | [NOIRLab noao-m34](https://noirlab.edu/public/images/noao-m34/) (large, 2048×2048) | Same — site hero image |
| `m34-ccd-2005.jpg` | [Wikimedia: M34a.jpg](https://commons.wikimedia.org/wiki/File:M34a.jpg) (Ole Nielsen) | CC BY-SA 2.5 |
| `m34-dss1-1950s.jpg` | [SkyView DSS1 Red](https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?Survey=DSS1%20Red&Position=40.675%2C42.76&Size=0.583333&Pixels=800&Sampler=Clip&Return=JPEG) | STScI/AURA DSS copyright — see [DSS acknowledgements](https://archive.stsci.edu/dss/copyright.html) |
| `m34-dss2-1990s.jpg` | [SkyView DSS2 Red](https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?Survey=DSS2%20Red&Position=40.675%2C42.76&Size=0.583333&Pixels=800&Sampler=Clip&Return=JPEG) | Same as DSS |
| `m34-sdss-g.jpg` | [SkyView SDSS g](https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?Survey=SDSS%20g&Position=40.675%2C42.76&Size=0.583333&Pixels=800&Sampler=Clip&Return=JPEG) | SDSS — see [SDSS acknowledgements](https://www.sdss.org/collaboration/credits/) |
| `m34-wise-ir.jpg` | [SkyView WISE 22 µm](https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?Survey=WISE%2022&Position=40.675%2C42.76&Size=0.583333&Pixels=800&Sampler=Clip&Return=JPEG) | WISE / IPAC / Caltech / NASA |

Slider pairs use only the SkyView rows above (identical Position, Size, Pixels). NOIRLab and Wikimedia assets are kept for reference but are not mixed into the compare slider because they use independent plate solutions.

Re-download all assets: `bash research/scripts/fetch_sky_images.sh` from the repo root.

**Note:** JWST has not released a dedicated image of NGC 1039 (M34). The infrared comparison uses WISE archive data to illustrate mid-IR contrast, not a Webb observation.
