import type { AtlasBrightStar } from '../../data/atlasSkyOverlay';
import type { AtlasStar } from '../../data/atlasTypes';

export type AtlasPick =
  | { type: 'member'; star: AtlasStar }
  | { type: 'bright'; star: AtlasBrightStar };
