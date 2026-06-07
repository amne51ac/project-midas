export interface AtlasCluster {
  id: string;
  name: string;
  ra: number;
  dec: number;
  radiusDeg: number;
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
}

export interface AtlasBundle {
  meta: {
    modelVersion: string;
    nStars: number;
    holdoutClusterIds: string[];
    holdoutF1: number | null;
    builtFrom: string;
  };
  clusters: AtlasCluster[];
  stars: AtlasStar[];
}
