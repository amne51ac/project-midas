import { useState } from 'react';
import { ImageCompare, type CompareImage } from './ImageCompare';

const base = import.meta.env.BASE_URL;

const COMPARISONS: { id: string; title: string; note: string; before: CompareImage; after: CompareImage }[] = [
  {
    id: 'plates',
    title: 'Photographic plates → digital survey',
    note: 'Both frames are pulled from NASA SkyView with identical pointing and scale (0.58° field, 800×800 px). The left is a digitized POSS-I red plate (~1950s); the right is SDSS g-band CCD photometry (~2000s). Stars stay fixed as you slide.',
    before: {
      src: `${base}images/m34-dss1-1950s.jpg`,
      label: 'DSS1 · ~1950s plate',
      caption: 'Digitized Sky Survey (POSS-I red plate). Grain, plate defects, and limited dynamic range — yet this is how M34 was measured for decades.',
      credit: 'NASA/GSFC SkyView · DSS1 · STScI/AURA',
    },
    after: {
      src: `${base}images/m34-sdss-g.jpg`,
      label: 'SDSS · g band',
      caption: 'Sloan Digital Sky Survey CCD imaging — sharper, deeper, and uniformly calibrated across the same field as the plate.',
      credit: 'NASA/GSFC SkyView · SDSS',
    },
  },
  {
    id: 'optical-ir',
    title: 'Visible light → infrared',
    note: 'Webb has not observed M34. This pair uses the same SkyView geometry: SDSS g (optical) versus WISE 22 µm (mid-infrared). Cooler stars and dust stand out in IR without shifting the star positions.',
    before: {
      src: `${base}images/m34-sdss-g.jpg`,
      label: 'SDSS · g band',
      caption: 'Optical light near 480 nm. Bright blue main-sequence stars dominate; cluster members at ~200 Myr look similar in color.',
      credit: 'NASA/GSFC SkyView · SDSS',
    },
    after: {
      src: `${base}images/m34-wise-ir.jpg`,
      label: 'WISE · 22 µm IR',
      caption: 'Wide-field Infrared Survey Explorer at 22 microns. Mid-infrared emission highlights dust and cooler stars — the regime where JWST operates, though Webb has not targeted M34.',
      credit: 'NASA/GSFC SkyView · WISE / IPAC / Caltech',
    },
  },
  {
    id: 'amateur',
    title: 'First-generation → second-generation survey',
    note: 'DSS2 red-digitized plates (1990s) versus SDSS g (2000s CCD). Same astrometric grid — compare how survey technology changed while the star field stays locked in place.',
    before: {
      src: `${base}images/m34-dss2-1990s.jpg`,
      label: 'DSS2 · 1990s survey',
      caption: 'Second-generation Palomar Sky Survey digitization — sharper plates and better photometry than DSS1, still survey-grade.',
      credit: 'NASA/GSFC SkyView · DSS2 · STScI/AURA',
    },
    after: {
      src: `${base}images/m34-sdss-g.jpg`,
      label: 'SDSS · g band',
      caption: 'Modern CCD survey photometry on the identical field. Dedicated amateur stacks (like Ole Nielsen\'s M34 image) reach similar depth but use independent plate solutions — harder to align in a slider.',
      credit: 'NASA/GSFC SkyView · SDSS',
    },
  },
];

export function SkyImagery() {
  const [active, setActive] = useState(0);
  const comp = COMPARISONS[active];

  return (
    <div className="sky-imagery">
      <div className="sky-imagery__callout">
        <h3>About Hubble and Webb</h3>
        <p>
          There is <strong>no published Hubble or JWST mosaic of Messier 34</strong> (NGC 1039). Hubble&apos;s
          narrow field and scheduling priorities favor smaller or more distant targets; M34 spans ~35 arcminutes
          on the sky — wider than Hubble&apos;s camera — and its stars are already resolved from the ground.
        </p>
        <p>
          Names collide in the literature: <em>HH 34</em> is a young-star jet (Hubble has spectacular images), and{' '}
          <em>Caldwell 34</em> is a nebula in Orion — neither is this open cluster. Webb likewise has not released
          an M34 program; its early cluster work focused on regions like NGC 604 and nearby galaxy disks.
        </p>
        <p>
          What we <em>do</em> have is a rich archive of <strong>ground-based visible photography</strong> spanning
          photographic plates to modern CCDs, plus <strong>infrared all-sky surveys</strong> that foreshadow what
          space telescopes see at longer wavelengths.
        </p>
      </div>

      <div className="sky-imagery__tabs" role="tablist" aria-label="Image comparisons">
        {COMPARISONS.map((c, i) => (
          <button
            key={c.id}
            type="button"
            role="tab"
            aria-selected={active === i}
            className={`sky-imagery__tab${active === i ? ' is-active' : ''}`}
            onClick={() => setActive(i)}
          >
            {c.title}
          </button>
        ))}
      </div>

      <p className="sky-imagery__note">{comp.note}</p>

      <ImageCompare before={comp.before} after={comp.after} initialPosition={48} />
    </div>
  );
}
