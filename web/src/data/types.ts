export interface Star {
  id: number;
  x: number;
  y: number;
  ra: number;
  dec: number;
  v: number;
  bv: number;
  mv: number;
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
  meta: { n_total: number; n_sample: number; distance_pc: number };
}
