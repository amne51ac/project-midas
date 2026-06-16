export interface AtlasCluster {
  id: string;
  name: string;
  ra: number;
  dec: number;
  radiusDeg: number;
  trust?: {
    registryTier?: string;
    separation?: number;
    predPosRate?: number;
    nScored?: number;
  };
}

export interface AtlasStar {
  id: number;
  clusterId: string;
  ra: number;
  dec: number;
  g?: number;
  pMember?: number;
  pBinary: number;
  malofeeva: number;
  trustScore?: number;
  trustTier?: string;
  recommendedUse?: string;
  pInterval90Low?: number;
  pInterval90High?: number;
  rankPct?: number | null;
  clusterSeparation?: number;
}

export interface AtlasBundle {
  meta: {
    modelVersion: string;
    nStars: number;
    nClusters?: number;
    holdoutClusterIds: string[];
    holdoutF1: number | null;
    builtFrom: string;
    trustSchema?: string;
    tier?: string;
  };
  clusters: AtlasCluster[];
  stars: AtlasStar[];
}
