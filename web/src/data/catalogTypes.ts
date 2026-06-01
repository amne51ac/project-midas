export interface CatalogPoint {
  id: string | number;
  ra: number;
  dec: number;
  x?: number;
  y?: number;
  mag?: number;
  bv?: number;
  mv?: number;
  plx?: number;
  pmra?: number;
  pmdec?: number;
  prob?: number;
  cgMember?: boolean;
  gaiaId?: string;
  excelSingle?: boolean;
  excelBinary?: boolean;
  malofeeva?: boolean;
  wocs?: boolean;
  bv0?: number;
  mv0?: number;
  period?: number;
  rv?: number;
  rvProb?: number;
  rotSeq?: string;
  w2bpk?: number;
  hw2w1?: number;
  mem?: string;
}

export interface CatalogLayer {
  id: string;
  name: string;
  shortName: string;
  color: string;
  description: string;
  totalCount: number;
  sampleCount: number;
  hasPlateCoords?: boolean;
  points: CatalogPoint[];
}

export interface PublishedCatalog {
  id: string;
  name: string;
  totalCount: number;
  note: string;
  renderable: false;
}

export interface CatalogBundle {
  center: { ra: number; dec: number };
  radiusDeg: number;
  layers: CatalogLayer[];
  published: PublishedCatalog[];
  meta: {
    distance_pc: number;
    ebv?: number;
    cg_member_threshold?: number;
    built_from: (string | null)[];
  };
}
