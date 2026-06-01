export interface Star {
  id: number;
  x: number;
  y: number;
  ra: number;
  dec: number;
  v: number;
  bv: number;
  mv: number;
  /** De-reddened B−V (E(B−V) applied in join table) */
  bv0?: number;
  /** De-reddened absolute V */
  mv0?: number;
  cgProba?: number;
  cgMember?: boolean;
  gaiaId?: string;
  excelSingle?: boolean;
  excelBinary?: boolean;
  malofeeva?: boolean;
  wocs?: boolean;
  wocsSeq?: string;
}

export interface HistoryEvent {
  era: string;
  title: string;
  summary: string;
  detail: string;
}

export interface DatasetMeta {
  stars: Star[];
  isochrone: { mv: number; bv: number }[];
  history: HistoryEvent[];
  meta: {
    n_total: number;
    n_sample: number;
    distance_pc: number;
    ebv?: number;
    cg_member_threshold?: number;
    n_cg_members?: number;
    n_gaia_matched?: number;
    built_from?: string;
  };
}
