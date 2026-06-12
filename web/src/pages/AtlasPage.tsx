import { useEffect } from 'react';
import { Header } from '../components/Header';
import { CredenceAtlas } from '../components/CredenceAtlas';
import atlasBundle from '../data/atlasT0.json';
import type { AtlasBundle } from '../data/atlasTypes';

const bundle = atlasBundle as AtlasBundle;

export function AtlasPage() {
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
