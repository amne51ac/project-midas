import { useEffect, useMemo } from 'react';
import { Header } from '../components/Header';
import { CredenceAtlas } from '../components/CredenceAtlas';
import atlasT0 from '../data/atlasT0.json';
import atlasT1Pilot from '../data/atlasT1Pilot.json';
import type { AtlasBundle } from '../data/atlasTypes';

const t1Bundle = atlasT1Pilot as AtlasBundle;
const t0Bundle = atlasT0 as AtlasBundle;

function pickBundle(): AtlasBundle {
  if (t1Bundle.meta?.nClusters && t1Bundle.meta.nClusters > 0) {
    return t1Bundle;
  }
  return t0Bundle;
}

export function AtlasPage() {
  const bundle = useMemo(() => pickBundle(), []);

  useEffect(() => {
    document.body.classList.add('atlas-route');
    return () => document.body.classList.remove('atlas-route');
  }, []);

  return (
    <>
      <Header />
      <CredenceAtlas bundle={bundle} />
    </>
  );
}

export default AtlasPage;
