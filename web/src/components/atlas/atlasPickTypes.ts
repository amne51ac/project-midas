import type { AtlasReferenceObject } from '../../data/atlasReferenceObjects';
import type { AtlasStar } from '../../data/atlasTypes';

export type AtlasPick =
  | { type: 'member'; star: AtlasStar }
  | { type: 'bright'; star: AtlasReferenceObject };
