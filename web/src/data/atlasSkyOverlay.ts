/** Full-sky reference layers for Credence Atlas — merged exports. */

export { ATLAS_CONSTELLATION_DATA as ATLAS_CONSTELLATIONS } from './atlasConstellationData';
export type { AtlasConstellation } from './atlasConstellationData';

export {
  ATLAS_REFERENCE_OBJECTS,
  type AtlasReferenceKind,
  type AtlasReferenceObject,
} from './atlasReferenceObjects';

/** @deprecated Use AtlasReferenceObject */
export type AtlasBrightStar = import('./atlasReferenceObjects').AtlasReferenceObject;

import { ATLAS_REFERENCE_OBJECTS } from './atlasReferenceObjects';

export const ATLAS_BRIGHT_STARS = ATLAS_REFERENCE_OBJECTS;
