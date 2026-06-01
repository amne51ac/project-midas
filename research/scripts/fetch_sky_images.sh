#!/usr/bin/env bash
# Fetch M34 comparison images — all SkyView pairs share identical astrometry for slider alignment.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
IMGDIR="$ROOT/web/public/images"
mkdir -p "$IMGDIR"

# M34 (NGC 1039): RA 40.675°, Dec +42.76°, field ~35′ (0.583°)
# Every compare pair MUST use the same Position, Size, Pixels, and Sampler so stars register.
SKYVIEW="https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?Position=40.675%2C42.76&Sampler=Clip&Size=0.583333&Pixels=800&Return=JPEG"

curl -sL "${SKYVIEW}&Survey=DSS1%20Red" -o "$IMGDIR/m34-dss1-1950s.jpg"
curl -sL "${SKYVIEW}&Survey=DSS2%20Red" -o "$IMGDIR/m34-dss2-1990s.jpg"
curl -sL "${SKYVIEW}&Survey=SDSS%20g" -o "$IMGDIR/m34-sdss-g.jpg"
curl -sL "${SKYVIEW}&Survey=WISE%2022" -o "$IMGDIR/m34-wise-ir.jpg"

# Reference images (not used in aligned slider — different framing)
curl -sL "https://storage.noirlab.edu/media/archives/images/screen/noao-m34.jpg" -o "$IMGDIR/m34-noirlab-1996.jpg"
curl -sL "https://storage.noirlab.edu/media/archives/images/large/noao-m34.jpg" -o "$IMGDIR/m34-hero.jpg"
curl -sL "https://upload.wikimedia.org/wikipedia/commons/1/1c/M34a.jpg" -o "$IMGDIR/m34-ccd-2005.jpg"

echo "Saved to $IMGDIR:"
for f in "$IMGDIR"/m34-*.jpg; do
  echo "  $(basename "$f"): $(file -b "$f")"
done
