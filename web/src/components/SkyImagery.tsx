import { useState } from 'react';
import { ImageCompare, type CompareImage } from './ImageCompare';

const base = import.meta.env.BASE_URL;

const COMPARISONS: { id: string; title: string; note: string; before: CompareImage; after: CompareImage }[] = [
  {
    id: 'plates',
    title: 'Photographic plates → digital survey',
    note: 'Both images are visible light. The left is a digitized Palomar Sky Survey plate from the 1950s; the right is a true-color BVR composite from Kitt Peak (1996).',
    before: {
      src: `${base}images/m34-dss1-1950s.jpg`,
      label: 'DSS1 · ~1950s plate',
      caption: 'Digitized Sky Survey (POSS-I red plate). Grain, plate defects, and limited dynamic range — yet this is how M34 was measured for decades.',
      credit: 'NASA/GSFC SkyView · DSS1 · STScI/AURA',
    },
    after: {
      src: `${base}images/m34-noirlab-1996.jpg`,
      label: 'NOIRLab · 1996 BVR',
      caption: 'Burrell Schmidt telescope, Kitt Peak — approximately true-color CCD photometry across a 35′ field, matching the scale of the cluster.',
      credit: 'REU program / NOIRLab / NSF / AURA',
    },
  },
  {
    id: 'optical-ir',
    title: 'Visible light → infrared',
    note: 'Webb has not observed M34. This pair shows what changes when you leave the visible band: 2MASS near-infrared reveals cooler stars and different contrast — the same principle Webb uses, at lower resolution.',
    before: {
      src: `${base}images/m34-noirlab-1996.jpg`,
      label: 'Optical · visible',
      caption: 'Human-eye wavelengths (B, V, R). Bright blue stars dominate; many cluster members look similar at this age.',
      credit: 'REU program / NOIRLab / NSF / AURA',
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
    title: 'Survey camera → modern astrophotography',
    note: 'Amateur and professional wide-field imagers still target M34 because it is bright, large, and resolved into individual stars.',
    before: {
      src: `${base}images/m34-dss2-1990s.jpg`,
      label: 'DSS2 · 1990s survey',
      caption: 'Second-generation Palomar Sky Survey digitization — sharper plates, better photometry than DSS1, still survey-grade.',
      credit: 'NASA/GSFC SkyView · DSS2 · STScI/AURA',
    },
    after: {
      src: `${base}images/m34-ccd-2005.jpg`,
      label: 'CCD · 2005',
      caption: 'Dedicated amateur CCD stack (Ole Nielsen). Longer exposure, higher resolution, and deliberate color balance.',
      credit: 'Ole Nielsen / CC BY-SA 2.5 via Wikimedia Commons',
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
